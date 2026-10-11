"""RAG 问答编排：会话解析、检索、流式生成、引用、持久化。"""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from app.config import settings
from app.database import SessionLocal
from app.models import Conversation, KnowledgeBase, Message
from app.rag.chain import format_history, get_chain, rewrite_query
from app.rag.citation import build_context, parse_citations
from app.rag.embeddings import embed_query
from app.rag.retriever import retrieve
from app.services import semantic_cache

logger = logging.getLogger("rag.chat")

HISTORY_LIMIT = 8


def _sse(event_type: str, payload: dict | None = None) -> str:
    data = {"type": event_type}
    if payload:
        data.update(payload)
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _chunk_text(text: str, size: int = 12) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


def _mock_answer(question: str) -> str:
    """压测模式的模拟回答（零网络、零费用）。"""
    return (
        f"这是压测模式的模拟回答哦～关于「{question[:20]}」，"
        "根据知识库资料 [1]，相关信息已为你整理完毕，详情请以页面为准～"
    )


def _get_or_create_conversation(db, user_id: int, conversation_id: int | None) -> Conversation:
    if conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
        if conv:
            return conv
    conv = Conversation(user_id=user_id, title="新对话")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def _save_assistant(db, conversation_id: int, answer: str, sources: list, latency_ms: int) -> None:
    db.add(
        Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            citations=sources,
            latency_ms=latency_ms,
        )
    )
    db.commit()


async def chat_stream(user_id: int, conversation_id: int | None, message: str):
    """SSE 异步生成器，产出 delta / sources / done / error 事件。"""
    db = SessionLocal()
    started = time.time()
    try:
        conv = _get_or_create_conversation(db, user_id, conversation_id)
        cid = conv.id

        # 保存用户消息
        user_msg = Message(conversation_id=cid, role="user", content=message)
        db.add(user_msg)
        db.commit()

        # 首次提问设置标题
        if conv.title == "新对话":
            conv.title = message[:20]
            conv.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()

        # 历史消息（排除刚保存的用户消息）
        history_rows = (
            db.query(Message)
            .filter(Message.conversation_id == cid, Message.id != user_msg.id)
            .order_by(Message.id.desc())
            .limit(HISTORY_LIMIT)
            .all()
        )
        history_rows = list(reversed(history_rows))
        history_str = format_history(history_rows)

        try:
            # 查询改写（指代消解）
            query = message
            if settings.QUERY_REWRITE_ENABLED and not settings.MOCK_LLM and history_rows:
                query = await asyncio.to_thread(rewrite_query, history_str, message)

            # 单次 query 向量化，供语义缓存 + 向量检索复用
            query_embedding = await asyncio.to_thread(embed_query, query)

            # 语义缓存命中
            cached = semantic_cache.lookup(query_embedding)
            if cached is not None:
                answer, sources = cached
                for piece in _chunk_text(answer):
                    yield _sse("delta", {"content": piece})
                yield _sse("sources", {"sources": sources})
                _save_assistant(db, cid, answer, sources, int((time.time() - started) * 1000))
                yield _sse("done", {})
                return

            # 跨知识库检索
            kbs = db.query(KnowledgeBase).all()
            kb_meta = [(kb.id, kb.name) for kb in kbs]

            def _do_retrieve():
                out = []
                for kb_id, kb_name in kb_meta:
                    for c in retrieve(kb_id, query, settings.RETRIEVAL_TOP_K, query_embedding):
                        c["kb_id"] = kb_id
                        c["kb_name"] = kb_name
                        out.append(c)
                seen, dedup = set(), []
                for c in out:
                    key = c["content"]
                    if key in seen:
                        continue
                    seen.add(key)
                    dedup.append(c)
                dedup.sort(key=lambda x: x["score"], reverse=True)
                return dedup[: settings.RETRIEVAL_TOP_K]

            citations = await asyncio.to_thread(_do_retrieve)
            context = build_context(citations)

            answer_parts: list[str] = []
            if settings.MOCK_LLM:
                for piece in _chunk_text(_mock_answer(message), size=4):
                    answer_parts.append(piece)
                    yield _sse("delta", {"content": piece})
                    if settings.MOCK_LLM_DELAY_MS > 0:
                        await asyncio.sleep(settings.MOCK_LLM_DELAY_MS / 1000)
            else:
                chain = get_chain()
                async for chunk in chain.astream(
                    {"history": history_str, "context": context, "question": message}
                ):
                    answer_parts.append(chunk)
                    yield _sse("delta", {"content": chunk})

            answer = "".join(answer_parts)
            sources = parse_citations(answer, citations)
            # 兜底：模型未显式标注 [n] 时，仍展示检索到的前 3 条片段
            if not sources and citations:
                sources = [{**c, "index": i + 1} for i, c in enumerate(citations[:3])]

            _save_assistant(db, cid, answer, sources, int((time.time() - started) * 1000))
            semantic_cache.store(query_embedding, (answer, sources))

            yield _sse("sources", {"sources": sources})
            yield _sse("done", {})
        except Exception as e:  # noqa: BLE001
            logger.exception("问答处理失败")
            yield _sse("error", {"message": f"处理失败：{e}"})
            yield _sse("done", {})
    finally:
        db.close()

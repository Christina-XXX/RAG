"""检索：混合检索（向量 + BM25，RRF 融合）+ 重排序（gte-rerank）。"""
from typing import List

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from app.config import settings
from app.rag.vectorstore import get_vectorstore

# 每个知识库的 BM25 索引缓存（文档增删后失效）
_bm25_cache: dict[int, BM25Retriever] = {}


def invalidate_bm25(kb_id: int) -> None:
    _bm25_cache.pop(kb_id, None)


def _load_all_docs(vectorstore) -> List[Document]:
    data = vectorstore.get(include=["documents", "metadatas"])
    documents = data.get("documents") or []
    metadatas = data.get("metadatas") or []
    docs = []
    for i, content in enumerate(documents):
        meta = metadatas[i] if i < len(metadatas) else {}
        docs.append(Document(page_content=content, metadata=meta or {}))
    return docs


def _get_bm25(kb_id: int, vectorstore) -> BM25Retriever | None:
    if kb_id not in _bm25_cache:
        docs = _load_all_docs(vectorstore)
        _bm25_cache[kb_id] = BM25Retriever.from_documents(docs, k=50) if docs else None
    return _bm25_cache[kb_id]


def _rrf_merge(vec_docs: List[Document], bm25_docs: List[Document], k: int = 60):
    """RRF 融合：score = sum(1/(k+rank))，只依赖排名。"""
    scored: dict[str, dict] = {}
    for rank, doc in enumerate(vec_docs):
        key = doc.page_content
        if key not in scored:
            scored[key] = {"doc": doc, "score": 0.0}
        scored[key]["score"] += 1.0 / (k + rank + 1)
    for rank, doc in enumerate(bm25_docs):
        key = doc.page_content
        if key not in scored:
            scored[key] = {"doc": doc, "score": 0.0}
        scored[key]["score"] += 1.0 / (k + rank + 1)
    ranked = sorted(scored.values(), key=lambda x: x["score"], reverse=True)
    return [(item["doc"], item["score"]) for item in ranked]


def _rerank(query: str, docs: List[Document], top_n: int) -> List[tuple]:
    """百炼 gte-rerank 重排序，返回 [(doc, relevance_score)]。"""
    from dashscope import TextReRank

    try:
        resp = TextReRank.call(
            model=settings.RERANK_MODEL,
            query=query,
            documents=[d.page_content for d in docs],
            top_n=min(top_n, len(docs)),
            return_documents=False,
        )
        if resp.status_code == 200 and resp.output and resp.output.results:
            out = []
            for r in resp.output.results:
                idx = r.get("index")
                score = float(r.get("relevance_score", 0.0))
                if idx is not None and 0 <= idx < len(docs):
                    out.append((docs[idx], score))
            if out:
                return out
    except Exception:
        pass
    return [(d, 0.0) for d in docs[:top_n]]


def retrieve(
    kb_id: int, query: str, top_k: int | None = None, query_embedding=None
) -> List[dict]:
    """返回引用列表 [{content, source, score, doc_id, chunk_index}]。"""
    top_k = top_k or settings.RETRIEVAL_TOP_K
    vectorstore = get_vectorstore(kb_id)

    if query_embedding is not None:
        vec_docs = vectorstore.similarity_search_by_vector(
            query_embedding, k=max(top_k * 3, 10)
        )
    else:
        vec_hits = vectorstore.similarity_search_with_score(query, k=max(top_k * 3, 10))
        vec_docs = [d for d, _ in vec_hits]

    bm25_docs: List[Document] = []
    if settings.HYBRID_ENABLED:
        bm25 = _get_bm25(kb_id, vectorstore)
        if bm25:
            bm25_docs = bm25.invoke(query)

    ranked = _rrf_merge(vec_docs, bm25_docs)

    if settings.RERANK_ENABLED and len(ranked) > top_k:
        pairs = _rerank(query, [d for d, _ in ranked], top_k)
        final = [{"doc": d, "score": round(s, 4)} for d, s in pairs]
    else:
        final = [{"doc": d, "score": round(s, 4)} for d, s in ranked[:top_k]]

    citations = []
    for item in final:
        doc = item["doc"]
        meta = doc.metadata or {}
        citations.append(
            {
                "content": doc.page_content,
                "source": meta.get("source", "未知来源"),
                "score": item["score"],
                "doc_id": meta.get("doc_id"),
                "chunk_index": meta.get("chunk_index"),
            }
        )
    return citations

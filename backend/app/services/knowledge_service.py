"""知识库文档摄取与删除（后台任务）。"""
import hashlib

from app.database import SessionLocal
from app.models import Document, KnowledgeBase
from app.rag.loader import load_document_bytes
from app.rag.retriever import invalidate_bm25
from app.rag.splitter import get_splitter
from app.rag.vectorstore import get_vectorstore

ALLOWED_EXTS = {"pdf", "docx", "txt", "md", "markdown", "csv", "xlsx"}


def file_ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def file_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def ingest_document(kb_id: int, doc_id: int, filename: str, data: bytes) -> None:
    """后台执行：加载 -> 切分 -> 向量化 -> 写入 Chroma。使用独立会话。"""
    db = SessionLocal()
    try:
        doc = db.get(Document, doc_id)
        if doc is None:
            return
        try:
            lc_docs = load_document_bytes(filename, data)
            if not lc_docs:
                raise ValueError("文档内容为空")

            chunks = get_splitter().split_documents(lc_docs)
            if not chunks:
                raise ValueError("切分后无内容")

            texts, metadatas = [], []
            for i, c in enumerate(chunks):
                c.metadata.update(
                    {
                        "doc_id": doc_id,
                        "kb_id": kb_id,
                        "source": filename,
                        "chunk_index": i,
                    }
                )
                texts.append(c.page_content)
                metadatas.append(c.metadata)

            get_vectorstore(kb_id).add_texts(texts=texts, metadatas=metadatas)
            invalidate_bm25(kb_id)

            doc.status = "done"
            doc.chunk_count = len(chunks)
            kb = db.get(KnowledgeBase, kb_id)
            if kb:
                kb.chunk_count = (kb.chunk_count or 0) + len(chunks)
                kb.doc_count = (kb.doc_count or 0) + 1
            db.commit()
        except Exception as e:  # noqa: BLE001
            doc.status = "failed"
            db.commit()
            print(f"[ingest] 文档 {filename} 摄取失败: {e}")
    finally:
        db.close()


def delete_document(kb_id: int, doc_id: int) -> None:
    db = SessionLocal()
    try:
        doc = db.get(Document, doc_id)
        if doc is None or doc.kb_id != kb_id:
            return
        try:
            get_vectorstore(kb_id).delete(where={"doc_id": doc_id})
        except Exception as e:  # noqa: BLE001
            print(f"[delete] 删除向量失败: {e}")
        invalidate_bm25(kb_id)

        kb = db.get(KnowledgeBase, kb_id)
        if kb:
            kb.chunk_count = max(0, (kb.chunk_count or 0) - (doc.chunk_count or 0))
            kb.doc_count = max(0, (kb.doc_count or 0) - 1)
        db.delete(doc)
        db.commit()
    finally:
        db.close()

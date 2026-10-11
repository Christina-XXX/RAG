"""Chroma 向量库：每个知识库一个 collection。"""
from functools import lru_cache

import chromadb
from langchain_community.vectorstores import Chroma

from app.config import settings
from app.rag.embeddings import get_embeddings


@lru_cache
def _get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def collection_name(kb_id: int) -> str:
    return f"kb_{kb_id}"


def get_vectorstore(kb_id: int) -> Chroma:
    client = _get_client()
    # 确保 collection 存在（text-embedding-v3 输出已归一化，默认距离即可）
    client.get_or_create_collection(name=collection_name(kb_id))
    return Chroma(
        client=client,
        collection_name=collection_name(kb_id),
        embedding_function=get_embeddings(),
    )


def delete_vectorstore(kb_id: int) -> None:
    try:
        _get_client().delete_collection(collection_name(kb_id))
    except Exception:
        pass

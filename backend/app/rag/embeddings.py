"""向量化（Embedding）：百炼 text-embedding-v3，全局单例复用。"""
from functools import lru_cache

from langchain_community.embeddings import DashScopeEmbeddings

from app.config import settings


@lru_cache
def get_embeddings() -> DashScopeEmbeddings:
    return DashScopeEmbeddings(
        model=settings.EMBEDDING_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY or None,
    )


def embed_query(text: str) -> list[float]:
    """对查询文本向量化（供语义缓存与向量检索复用）。"""
    return get_embeddings().embed_query(text)

"""向量化（Embedding）：百炼 text-embedding-v3，全局单例复用。压测可切换本地模拟。"""
import hashlib
from functools import lru_cache

from langchain_community.embeddings import DashScopeEmbeddings

from app.config import settings


class FakeEmbeddings:
    """本地确定性假向量（压测用，零网络、零费用）。

    维度对齐 text-embedding-v3 = 1024，保证与已有 Chroma 数据维度兼容。
    同一文本永远得到同一向量（确定性，可用于语义缓存）。
    """

    def __init__(self, size: int = 1024):
        self.size = size

    def _embed(self, text: str) -> list[float]:
        seed = int.from_bytes(hashlib.md5(text.encode("utf-8")).digest()[:8], "big")
        x = seed
        vec = []
        for _ in range(self.size):
            x = (x * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
            vec.append((x >> 40) / (1 << 24) - 1.0)  # 归一化到 [-1, 1]
        return vec

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]


@lru_cache
def get_embeddings():
    if settings.MOCK_LLM:
        return FakeEmbeddings()
    return DashScopeEmbeddings(
        model=settings.EMBEDDING_MODEL,
        dashscope_api_key=settings.DASHSCOPE_API_KEY or None,
    )


def embed_query(text: str) -> list[float]:
    """对查询文本向量化（供语义缓存与向量检索复用）。"""
    return get_embeddings().embed_query(text)

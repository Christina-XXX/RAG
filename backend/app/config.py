"""全局配置：通过 pydantic-settings 读取环境变量 / .env 文件。"""
import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "RAG 知识库问答系统"

    # 安全（>= 32 字节，生产环境务必自行修改）
    SECRET_KEY: str = "9f2c7b1e4a8d6f3c5e2b9a7d1f4c8e6b0a3d5f7c9e1b4a6d8f0c2e5b7a9d1f3a5c7e9b"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # 数据库 / 向量库（绝对路径，避免受启动目录影响）
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'data' / 'rag.db').as_posix()}"
    CHROMA_PERSIST_DIR: str = (BASE_DIR / 'data' / 'chroma').as_posix()

    # 百炼（DashScope）
    DASHSCOPE_API_KEY: str = ""
    LLM_MODEL: str = "qwen-plus"
    EMBEDDING_MODEL: str = "text-embedding-v3"
    RERANK_MODEL: str = "gte-rerank-v2"

    # RAG 参数
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    RETRIEVAL_TOP_K: int = 6
    RERANK_ENABLED: bool = True
    HYBRID_ENABLED: bool = True
    QUERY_REWRITE_ENABLED: bool = True
    SEMANTIC_CACHE_ENABLED: bool = True

    # 压测/离线模式：true 时向量化、LLM、重排序全部本地模拟（零费用、无网络）
    MOCK_LLM: bool = False
    MOCK_LLM_DELAY_MS: int = 30  # 模拟 LLM 每个分块的延迟（毫秒）

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # 把 Key 注入环境变量，供 dashscope SDK / LangChain 自动读取
    if s.DASHSCOPE_API_KEY:
        os.environ["DASHSCOPE_API_KEY"] = s.DASHSCOPE_API_KEY
    return s


settings = get_settings()

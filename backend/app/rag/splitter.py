"""中文友好的文本切分。"""
from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


@lru_cache
def get_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        keep_separator=True,
    )

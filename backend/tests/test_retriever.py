"""RRF 融合（纯函数，无网络）。"""
from langchain_core.documents import Document

from app.rag.retriever import _rrf_merge


def test_rrf_ranks_common_doc_first():
    common = Document(page_content="common")
    only_vec = Document(page_content="only_vec")
    only_bm25 = Document(page_content="only_bm25")
    vec = [only_vec, common]  # 向量排名：only_vec 第1，common 第2
    bm25 = [common, only_bm25]  # BM25 排名：common 第1，only_bm25 第2

    result = _rrf_merge(vec, bm25)
    docs = [d for d, _ in result]
    # 出现在两个列表中的 common 应排第一
    assert docs[0].page_content == "common"


def test_rrf_deduplicates_same_content():
    d = Document(page_content="x")
    result = _rrf_merge([d], [d])
    assert len(result) == 1


def test_rrf_empty():
    assert _rrf_merge([], []) == []

"""引用上下文拼接与编号解析。"""
from app.rag.citation import build_context, parse_citations


def test_build_context_numbering():
    cits = [{"source": "a.md", "content": "AAA"}, {"source": "b.md", "content": "BBB"}]
    ctx = build_context(cits)
    assert "[1]" in ctx and "[2]" in ctx
    assert "a.md" in ctx and "AAA" in ctx


def test_parse_citations_maps_index():
    cits = [{"source": "a.md", "content": "A"}, {"source": "b.md", "content": "B"}]
    answer = "价格 4299 元 [1]，颜色有黑色 [2]。"
    sources = parse_citations(answer, cits)
    assert [s["index"] for s in sources] == [1, 2]
    assert sources[0]["content"] == "A"


def test_parse_citations_ignores_out_of_range():
    cits = [{"source": "a.md", "content": "A"}]
    sources = parse_citations("答案 [5] 与 [1]", cits)
    assert [s["index"] for s in sources] == [1]


def test_parse_citations_empty_when_no_marker():
    cits = [{"source": "a.md", "content": "A"}]
    assert parse_citations("没有任何标注", cits) == []

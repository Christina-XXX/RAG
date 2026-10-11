"""语义缓存。"""
from app.services.semantic_cache import SemanticCache


def test_put_and_get_exact():
    c = SemanticCache(threshold=0.9)
    c.put([1.0, 0.0, 0.0], ("answer", [{"index": 1}]))
    assert c.get([1.0, 0.0, 0.0]) is not None


def test_hit_on_similar_embedding():
    c = SemanticCache(threshold=0.9)
    c.put([1.0, 0.0, 0.0], "x")
    assert c.get([0.99, 0.1, 0.0]) == "x"


def test_miss_on_orthogonal():
    c = SemanticCache(threshold=0.95)
    c.put([1.0, 0.0], "x")
    assert c.get([0.0, 1.0]) is None


def test_miss_when_empty():
    c = SemanticCache()
    assert c.get([1.0, 0.0]) is None

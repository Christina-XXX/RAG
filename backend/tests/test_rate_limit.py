"""滑动窗口限流。"""
import pytest
from fastapi import HTTPException

from app.core.rate_limit import SimpleRateLimiter


class _Req:
    def __init__(self, host: str):
        self.client = type("Client", (), {"host": host})()


def test_under_limit_passes():
    limiter = SimpleRateLimiter(limit=3, window=60)
    for _ in range(3):
        limiter(_Req("1.2.3.4"))  # 不应抛异常


def test_over_limit_raises_429():
    limiter = SimpleRateLimiter(limit=2, window=60)
    limiter(_Req("1.1.1.1"))
    limiter(_Req("1.1.1.1"))
    with pytest.raises(HTTPException) as e:
        limiter(_Req("1.1.1.1"))
    assert e.value.status_code == 429


def test_different_clients_isolated():
    limiter = SimpleRateLimiter(limit=1, window=60)
    limiter(_Req("1.1.1.1"))
    limiter(_Req("2.2.2.2"))  # 不同 IP 不受影响

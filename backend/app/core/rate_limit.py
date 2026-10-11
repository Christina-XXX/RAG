"""轻量内存限流（滑动窗口），避免对异步 SSE 端点引入额外依赖。"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class SimpleRateLimiter:
    def __init__(self, limit: int = 30, window: int = 60):
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque] = defaultdict(deque)

    def __call__(self, request: Request):
        key = request.client.host if request.client else "unknown"
        now = time.time()
        q = self._hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            raise HTTPException(429, "请求过于频繁，请稍后再试")
        q.append(now)


chat_limiter = SimpleRateLimiter(limit=30, window=60)

"""Locust 压测脚本：单 User 类 + 任务级标签，用 --tags 选择场景。

运行示例（backend 目录下，--host 指向 mock 模式后端）：

  场景 A（认证+会话，不触发 LLM）：
    .venv/Scripts/python.exe -m locust -f tests/load/locustfile.py --host http://127.0.0.1:8001 \
        --tags light -u 100 -r 10 -t 3m --headless --csv=result_light

  场景 B（知识库问答，RAG 全链路）：
    .venv/Scripts/python.exe -m locust -f tests/load/locustfile.py --host http://127.0.0.1:8001 \
        --tags chat -u 100 -r 10 -t 3m --headless --csv=result_chat

  场景 C（混合真实负载）：
    .venv/Scripts/python.exe -m locust -f tests/load/locustfile.py --host http://127.0.0.1:8001 \
        --tags mixed -u 100 -r 10 -t 3m --headless --csv=result_mixed

说明：
  -u 100  最终并发用户数；-r 10  每秒新增用户数（爬坡）；-t 3m  运行 3 分钟。
  去掉 --headless 可打开 Locust Web 界面（http://localhost:8089）手动控制。
"""
import itertools
import random

from locust import FastHttpUser, between, tag, task

PASSWORD = "load123"
QUESTIONS = [
    "保温杯多少钱？",
    "保温杯有哪些颜色？",
    "保温效果怎么样？",
    "支持退换货吗？",
    "X20 Pro 手机的价格是多少？",
]

# 依次循环分配 load1..load100，保证 100 个并发用户尽量不重复
_usernames = itertools.cycle([f"load{i}" for i in range(1, 101)])


def _next_username() -> str:
    return next(_usernames)


class RagUser(FastHttpUser):
    wait_time = between(1.0, 3.0)

    def on_start(self):
        self.username = _next_username()
        r = self.client.post(
            "/api/auth/login",
            json={"username": self.username, "password": PASSWORD},
        )
        token = r.json().get("access_token", "") if r.status_code == 200 else ""
        self.headers = {"Authorization": f"Bearer {token}"}

    # ===== 场景 A：light（认证 + 会话/知识库浏览） =====
    @tag("light")
    @task(3)
    def list_conversations(self):
        self.client.get("/api/conversations", headers=self.headers)

    @tag("light", "mixed")
    @task(2)
    def create_conversation(self):
        self.client.post("/api/conversations", json={}, headers=self.headers)

    @tag("light")
    @task(1)
    def list_knowledge(self):
        self.client.get("/api/knowledge", headers=self.headers)

    # ===== 场景 B：chat（知识库问答，RAG 全链路 + 流式） =====
    @tag("chat", "mixed")
    @task(3)
    def chat(self):
        q = random.choice(QUESTIONS)
        self.client.post(
            "/api/chat",
            json={"message": q},
            headers=self.headers,
            name="/api/chat",
        )

    # ===== 场景 C：mixed（混合真实负载） =====
    @tag("mixed")
    @task(5)
    def browse(self):
        self.client.get("/api/conversations", headers=self.headers)

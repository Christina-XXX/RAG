"""压测数据准备：批量创建 100 个测试用户，并确保存在一个知识库（含示例文档）。

用法（先以 MOCK_LLM=true 启动后端，再在 backend 目录下执行）：
    .venv/Scripts/python.exe tests/load/prepare_data.py
"""
import os
import time
from pathlib import Path

import httpx

BASE = os.environ.get("RAG_BASE_URL", "http://127.0.0.1:8000")
USER_COUNT = 100
PASSWORD = "load123"
SAMPLE = Path(__file__).resolve().parents[3] / "sample_data" / "电商商品FAQ.md"


def main() -> None:
    # 1. 管理员登录（用于知识库准备）
    admin_token = None
    r = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "123456"})
    if r.status_code == 200:
        admin_token = r.json()["access_token"]
        print("✅ 管理员登录成功")
    else:
        print("⚠️ 管理员登录失败，跳过知识库准备")

    # 2. 批量创建 100 个用户（已存在则跳过，返回 400）
    created = 0
    for i in range(1, USER_COUNT + 1):
        username = f"load{i}"
        rr = httpx.post(
            f"{BASE}/api/auth/register",
            json={"username": username, "password": PASSWORD},
        )
        if rr.status_code in (201, 400):
            created += 1
    print(f"✅ 用户就绪：load1 ~ load{USER_COUNT}（密码 {PASSWORD}），成功 {created}")

    # 3. 确保存在一个知识库
    if admin_token:
        H = {"Authorization": f"Bearer {admin_token}"}
        kbs = httpx.get(f"{BASE}/api/knowledge", headers=H).json()
        if not kbs:
            kb = httpx.post(
                f"{BASE}/api/knowledge",
                json={"name": "压测知识库", "description": "压测用"},
                headers=H,
            ).json()
            kb_id = kb["id"]
            with open(SAMPLE, "rb") as f:
                httpx.post(
                    f"{BASE}/api/knowledge/{kb_id}/documents",
                    headers=H,
                    files={"file": ("电商商品FAQ.md", f, "text/markdown")},
                )
            print("✅ 已创建「压测知识库」并上传示例文档")
            for _ in range(15):
                docs = httpx.get(f"{BASE}/api/knowledge/{kb_id}/documents", headers=H).json()
                if docs and all(d["status"] in ("done", "failed") for d in docs):
                    print("✅ 文档摄取完成")
                    break
                time.sleep(2)
        else:
            print(f"ℹ️ 已有 {len(kbs)} 个知识库，跳过创建")

    print("=== 数据准备完成 ===")


if __name__ == "__main__":
    main()

"""端到端验证脚本：建知识库 -> 上传示例文档 -> 摄取 -> 流式问答并打印引用。

用法（先启动后端，且在 backend 目录下）：
    .venv/Scripts/python.exe e2e_test.py
"""
import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"
SAMPLE = "../sample_data/电商商品FAQ.md"


def login(username: str, password: str) -> str:
    r = httpx.post(f"{BASE}/api/auth/login", json={"username": username, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def main():
    admin = login("admin", "123456")
    H = {"Authorization": f"Bearer {admin}"}

    # 1. 创建知识库
    r = httpx.post(f"{BASE}/api/knowledge", json={"name": "商品FAQ", "description": "电商商品知识库"}, headers=H)
    r.raise_for_status()
    kb = r.json()
    print(f"[1] 创建知识库: id={kb['id']} name={kb['name']}")

    # 2. 上传示例文档
    with open(SAMPLE, "rb") as f:
        r = httpx.post(
            f"{BASE}/api/knowledge/{kb['id']}/documents",
            headers=H,
            files={"file": ("电商商品FAQ.md", f, "text/markdown")},
        )
        r.raise_for_status()
        doc = r.json()
        print(f"[2] 上传文档: {doc['filename']} status={doc['status']}")

    # 3. 轮询摄取状态
    for _ in range(30):
        docs = httpx.get(f"{BASE}/api/knowledge/{kb['id']}/documents", headers=H).json()
        d = next(x for x in docs if x["id"] == doc["id"])
        if d["status"] in ("done", "failed"):
            print(f"[3] 摄取完成: status={d['status']} chunks={d['chunk_count']}")
            break
        time.sleep(2)
    else:
        print("[3] 摄取超时")
        sys.exit(1)

    # 4. 流式问答
    print("\n[4] 开始流式问答：'X20 Pro 多少钱？有什么颜色？'\n")
    with httpx.stream(
        "POST",
        f"{BASE}/api/chat",
        json={"message": "X20 Pro 多少钱？有什么颜色？"},
        headers=H,
        timeout=120,
    ) as resp:
        answer_parts = []
        sources = None
        for line in resp.iter_lines():
            if line.startswith("data: "):
                ev = json.loads(line[6:])
                if ev["type"] == "delta":
                    answer_parts.append(ev["content"])
                elif ev["type"] == "sources":
                    sources = ev["sources"]
                elif ev["type"] == "error":
                    print("  !! 错误:", ev["message"])
    print("回答：")
    print("".join(answer_parts))
    print(f"\n[5] 引用来源数: {len(sources) if sources else 0}")
    for s in sources or []:
        print(f"  [{s.get('index')}] {s.get('source')} -> {s.get('content')[:50]}...")

    print("\n=== 端到端验证完成 ===")


if __name__ == "__main__":
    main()

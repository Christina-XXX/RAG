"""会话管理：多用户隔离、历史消息、删除。"""


def _token(client, username, password="pass123"):
    return client.post(
        "/api/auth/login", json={"username": username, "password": password}
    ).json()["access_token"]


def test_conversation_isolation(client, make_user):
    make_user("u1")
    make_user("u2")
    t1 = _token(client, "u1")
    t2 = _token(client, "u2")

    r = client.post("/api/conversations", json={}, headers={"Authorization": f"Bearer {t1}"})
    assert r.status_code == 201
    cid = r.json()["id"]

    # u1 可见自己的会话消息（空）
    r = client.get(f"/api/conversations/{cid}/messages", headers={"Authorization": f"Bearer {t1}"})
    assert r.status_code == 200
    assert r.json() == []

    # u2 无法访问 u1 的会话
    assert (
        client.get(
            f"/api/conversations/{cid}/messages", headers={"Authorization": f"Bearer {t2}"}
        ).status_code
        == 404
    )

    # 会话列表隔离
    assert len(client.get("/api/conversations", headers={"Authorization": f"Bearer {t1}"}).json()) == 1
    assert client.get("/api/conversations", headers={"Authorization": f"Bearer {t2}"}).json() == []


def test_delete_conversation(client, make_user):
    make_user("u3")
    t = _token(client, "u3")
    cid = client.post("/api/conversations", json={}, headers={"Authorization": f"Bearer {t}"}).json()["id"]

    r = client.delete(f"/api/conversations/{cid}", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    assert client.get("/api/conversations", headers={"Authorization": f"Bearer {t}"}).json() == []


def test_create_conversation_with_title(client, make_user):
    make_user("u4")
    t = _token(client, "u4")
    r = client.post("/api/conversations", json={"title": "自定义标题"}, headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 201
    assert r.json()["title"] == "自定义标题"

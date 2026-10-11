"""权限控制：仅管理员可访问知识库管理。"""


def _token(client, username, password="pass123"):
    return client.post(
        "/api/auth/login", json={"username": username, "password": password}
    ).json()["access_token"]


def test_anonymous_knowledge_access_401(client):
    assert client.get("/api/knowledge").status_code == 401


def test_normal_user_knowledge_access_ok(client, make_user):
    # 知识库管理对所有登录用户开放
    make_user("normal1")
    token = _token(client, "normal1")
    assert client.get("/api/knowledge", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_admin_knowledge_access_ok(client, make_user):
    make_user("boss1", is_admin=True)
    token = _token(client, "boss1")
    assert client.get("/api/knowledge", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_admin_stats_requires_admin(client, make_user):
    make_user("normal2")
    token = _token(client, "normal2")
    assert client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"}).status_code == 403

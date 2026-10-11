"""认证相关 API。"""


def test_register_returns_token_and_user(client):
    r = client.post("/api/auth/register", json={"username": "reg1", "password": "secret123"})
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"]
    assert body["user"]["username"] == "reg1"
    assert body["user"]["is_admin"] is False


def test_register_duplicate_username(client):
    client.post("/api/auth/register", json={"username": "dup1", "password": "secret123"})
    r = client.post("/api/auth/register", json={"username": "dup1", "password": "secret123"})
    assert r.status_code == 400


def test_register_short_password(client):
    r = client.post("/api/auth/register", json={"username": "short1", "password": "123"})
    assert r.status_code == 400


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"username": "wp1", "password": "secret123"})
    r = client.post("/api/auth/login", json={"username": "wp1", "password": "wrong"})
    assert r.status_code == 401


def test_change_password_flow(client):
    client.post("/api/auth/register", json={"username": "cp1", "password": "oldpass1"})
    token = client.post(
        "/api/auth/login", json={"username": "cp1", "password": "oldpass1"}
    ).json()["access_token"]

    r = client.post(
        "/api/auth/change-password",
        json={"old_password": "oldpass1", "new_password": "newpass1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200

    # 旧密码失效
    assert (
        client.post("/api/auth/login", json={"username": "cp1", "password": "oldpass1"}).status_code
        == 401
    )
    # 新密码可登录
    assert (
        client.post("/api/auth/login", json={"username": "cp1", "password": "newpass1"}).status_code
        == 200
    )


def test_change_password_wrong_old(client):
    client.post("/api/auth/register", json={"username": "cp2", "password": "oldpass1"})
    token = client.post(
        "/api/auth/login", json={"username": "cp2", "password": "oldpass1"}
    ).json()["access_token"]
    r = client.post(
        "/api/auth/change-password",
        json={"old_password": "WRONG", "new_password": "newpass1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400

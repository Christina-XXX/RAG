"""密码哈希与 JWT。"""
import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_hash_is_salted():
    assert hash_password("same") != hash_password("same")


def test_jwt_roundtrip():
    token = create_access_token(42)
    payload = decode_access_token(token)
    assert payload["sub"] == "42"


def test_jwt_invalid_token_raises():
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("not-a-valid-token")

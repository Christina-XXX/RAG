"""测试环境：在导入 app 前注入独立的测试数据库 / 向量库路径，避免污染真实数据。"""
import os
import pathlib
import tempfile

_TEST_DIR = pathlib.Path(tempfile.mkdtemp(prefix="rag_unit_"))
os.environ["DATABASE_URL"] = f"sqlite:///{( _TEST_DIR / 'test.db').as_posix()}"
os.environ["CHROMA_PERSIST_DIR"] = str(_TEST_DIR / "chroma")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def make_user():
    def _make(username: str, password: str = "pass123", is_admin: bool = False) -> User:
        db = SessionLocal()
        try:
            user = User(
                username=username,
                password_hash=hash_password(password),
                is_admin=is_admin,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()

    return _make

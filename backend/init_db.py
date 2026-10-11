"""建表 + 初始化管理员 admin / 123456。

用法（在 backend 目录下）：
    .venv/Scripts/python.exe init_db.py
"""
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import User


def init() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if admin is None:
            db.add(
                User(
                    username="admin",
                    password_hash=hash_password("123456"),
                    is_admin=True,
                )
            )
            db.commit()
            print("✅ 已创建管理员：admin / 123456")
        else:
            print("ℹ️  管理员已存在，跳过")
    finally:
        db.close()


if __name__ == "__main__":
    init()

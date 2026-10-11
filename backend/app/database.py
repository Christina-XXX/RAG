"""SQLAlchemy 引擎与会话管理。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = {}
engine_kwargs: dict = {"pool_pre_ping": True}
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite 单文件：扩大连接池 + 忙等待超时，支撑并发读写（压测优化）
    connect_args = {"check_same_thread": False, "timeout": 30}
    engine_kwargs.update(pool_size=50, max_overflow=50)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

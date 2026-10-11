"""管理后台：统计与用户列表（仅管理员）。"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.database import get_db
from app.models import Conversation, Document, KnowledgeBase, Message, User
from app.schemas import StatsOut, UserOut

router = APIRouter(
    prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    return StatsOut(
        user_count=db.query(User).count(),
        conversation_count=db.query(Conversation).count(),
        message_count=db.query(Message).count(),
        kb_count=db.query(KnowledgeBase).count(),
        doc_count=db.query(Document).count(),
        chunk_count=db.query(func.coalesce(func.sum(KnowledgeBase.chunk_count), 0)).scalar()
        or 0,
    )


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id.asc()).all()

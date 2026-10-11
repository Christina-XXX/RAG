"""RAG 问答（SSE 流式）与消息反馈。"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rate_limit import chat_limiter
from app.database import get_db
from app.models import Conversation, Message, User
from app.schemas import ChatRequest, FeedbackRequest
from app.services.chat_service import chat_stream

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", dependencies=[Depends(chat_limiter)])
async def chat(payload: ChatRequest, user: User = Depends(get_current_user)):
    message = payload.message.strip()
    if not message:
        raise HTTPException(400, "问题不能为空")
    if len(message) > 4000:
        raise HTTPException(400, "问题过长")
    return StreamingResponse(
        chat_stream(user.id, payload.conversation_id, message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/messages/{message_id}/feedback")
def feedback(
    message_id: int,
    payload: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.feedback not in ("like", "dislike"):
        raise HTTPException(400, "反馈值非法")
    msg = (
        db.query(Message)
        .join(Conversation)
        .filter(Message.id == message_id, Conversation.user_id == user.id)
        .first()
    )
    if msg is None:
        raise HTTPException(404, "消息不存在")
    msg.feedback = payload.feedback
    db.commit()
    return {"message": "已记录反馈"}

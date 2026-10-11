"""Pydantic 请求/响应模型。"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


# ---------- Auth ----------
class UserCreate(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_admin: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Conversation ----------
class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    citations: Optional[list[Any]] = None
    latency_ms: int = 0
    feedback: Optional[str] = None
    created_at: datetime


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str


class FeedbackRequest(BaseModel):
    feedback: str  # like / dislike


# ---------- Knowledge Base ----------
class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str = ""


class KnowledgeBaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    doc_count: int
    chunk_count: int
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kb_id: int
    filename: str
    file_type: str
    status: str
    chunk_count: int
    size: int
    created_at: datetime


class StatsOut(BaseModel):
    user_count: int
    conversation_count: int
    message_count: int
    kb_count: int
    doc_count: int
    chunk_count: int

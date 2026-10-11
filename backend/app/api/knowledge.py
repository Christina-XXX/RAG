"""知识库管理（仅管理员）。"""
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Document, KnowledgeBase, User
from app.rag.vectorstore import delete_vectorstore
from app.schemas import (
    DocumentOut,
    KnowledgeBaseCreate,
    KnowledgeBaseOut,
)
from app.services.knowledge_service import (
    ALLOWED_EXTS,
    delete_document,
    file_ext,
    file_hash,
    ingest_document,
)

router = APIRouter(
    prefix="/api/knowledge", tags=["knowledge"], dependencies=[Depends(get_current_user)]
)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.get("", response_model=list[KnowledgeBaseOut])
def list_kbs(db: Session = Depends(get_db)):
    return db.query(KnowledgeBase).order_by(KnowledgeBase.id.desc()).all()


@router.post("", response_model=KnowledgeBaseOut, status_code=201)
def create_kb(
    payload: KnowledgeBaseCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    kb = KnowledgeBase(
        name=payload.name, description=payload.description, created_by=user.id
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb


@router.delete("/{kb_id}")
def delete_kb(kb_id: int, db: Session = Depends(get_db)):
    kb = db.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(404, "知识库不存在")
    db.query(Document).filter(Document.kb_id == kb_id).delete()
    db.delete(kb)
    db.commit()
    delete_vectorstore(kb_id)
    return {"message": "已删除"}


@router.get("/{kb_id}/documents", response_model=list[DocumentOut])
def list_documents(kb_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Document)
        .filter(Document.kb_id == kb_id)
        .order_by(Document.id.desc())
        .all()
    )


@router.post("/{kb_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    kb_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    kb = db.get(KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(404, "知识库不存在")

    filename = file.filename or ""
    ext = file_ext(filename)
    if ext not in ALLOWED_EXTS:
        raise HTTPException(400, f"不支持的文件类型: {ext or '未知'}")

    data = await file.read()
    if not data:
        raise HTTPException(400, "文件为空")
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(400, "文件过大（>50MB）")

    h = file_hash(data)
    dup = (
        db.query(Document)
        .filter(Document.kb_id == kb_id, Document.file_hash == h)
        .first()
    )
    if dup:
        raise HTTPException(409, "文件已存在（内容相同）")

    doc = Document(
        kb_id=kb_id,
        filename=filename,
        file_type=ext,
        status="processing",
        file_hash=h,
        size=len(data),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(ingest_document, kb_id, doc.id, filename, data)
    return doc


@router.delete("/{kb_id}/documents/{doc_id}")
def remove_document(kb_id: int, doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if doc is None or doc.kb_id != kb_id:
        raise HTTPException(404, "文档不存在")
    delete_document(kb_id, doc_id)
    return {"message": "已删除"}

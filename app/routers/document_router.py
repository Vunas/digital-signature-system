from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.document_schema import DocumentResponse
from app.services.file_service import file_service
from app.repositories.document_repo import document_repo

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload tệp PDF gốc lên hệ thống trước khi ký"""
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="Hệ thống chỉ chấp nhận định dạng PDF."
        )

    doc = await file_service.upload_document(db, current_user.id, file)
    return doc


@router.get("/", response_model=list[DocumentResponse])
def get_my_documents(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Lấy danh sách các tài liệu đã upload của người dùng"""
    return document_repo.get_all_by_user(db, current_user.id)

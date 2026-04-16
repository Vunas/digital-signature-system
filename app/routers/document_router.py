from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.document_schema import DocumentResponse
from app.services.file_service import file_service
from app.repositories.document_repo import document_repo

# ✅ IMPORT ĐÚNG (không dùng supabase trực tiếp nữa)
from app.utils.file_utils import get_file_content

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
    """Lấy danh sách các tài liệu của user"""
    return document_repo.get_all_by_user(db, current_user.id)


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    is_signed: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tải file PDF (local hoặc Supabase – tự động xử lý)
    """

    # 1. Kiểm tra document
    doc = document_repo.get_by_id(db, doc_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

    # 2. Xác định path
    file_path = doc.signed_file_path if is_signed else doc.original_file_path

    if not file_path:
        raise HTTPException(
            status_code=400,
            detail=(
                "Tài liệu này chưa được ký."
                if is_signed
                else "Không tìm thấy file gốc."
            ),
        )

    # 3. Lấy file content (🔥 FIX CHÍNH Ở ĐÂY)
    try:
        file_bytes = get_file_content(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Lỗi tải file từ Storage: {str(e)}"
        )

    # 4. Chuẩn hóa tên file
    filename = doc.file_name
    if is_signed and not filename.endswith("_signed.pdf"):
        filename = filename.replace(".pdf", "_signed.pdf")

    # 5. Stream file về client
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

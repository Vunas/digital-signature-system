from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import os
import shutil

from app.schemas.verify_schema import VerifyResponse
from app.services.verify_service import verify_service
from app.core.dependencies import get_db

router = APIRouter(prefix="/api/verify", tags=["Verification"])


@router.post("/pdf", response_model=VerifyResponse)
async def verify_uploaded_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),  # Bổ sung DB Session để dò Root CA
):
    """
    Xác thực một file PDF xem đã được ký chưa, có bị chỉnh sửa không
    và đối chiếu gốc chữ ký với Root CA trong Database.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="Vui lòng tải lên file định dạng PDF."
        )

    temp_path = f"temp_{file.filename}"
    try:
        # Reset con trỏ file về đầu (đảm bảo file không bị lỗi 0 bytes)
        file.file.seek(0)

        # Lưu tạm file để pyHanko đọc
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Xác thực file (Truyền thêm db vào)
        result = verify_service.verify_pdf_signature(db, temp_path)
        return result

    finally:
        # Xóa file tạm sau khi kiểm tra xong để giải phóng ổ cứng
        if os.path.exists(temp_path):
            os.remove(temp_path)

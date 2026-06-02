from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid
import aiofiles

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.verify_schema import VerifyResponse
from app.services.verify_service import verify_service
from app.utils.logger import logger

router = APIRouter(prefix="/api/verify", tags=["Verification"])


@router.post("/pdf", response_model=VerifyResponse)
async def verify_uploaded_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xác thực một file PDF xem đã được ký chưa, có bị chỉnh sửa không.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Vui lòng tải lên file định dạng PDF.")

    safe_filename = f"temp_verify_{uuid.uuid4().hex}.pdf"

    try:
        logger.info(
            f"User {current_user.username} đang thực hiện xác thực tài liệu PDF: {file.filename}"
        )

        # Đảm bảo con trỏ file nằm ở vị trí đầu tiên trước khi đọc
        await file.seek(0)

        # Sử dụng aiofiles để lưu file bất đồng bộ (tránh block I/O của Event Loop)
        async with aiofiles.open(safe_filename, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        result = await verify_service.verify_pdf_signature(db, safe_filename, current_user.id)

        await db.commit()

        return result

    except Exception as e:
        await db.rollback()
        logger.error(f"Lỗi hệ thống khi verify PDF ({file.filename}): {str(e)}")
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi trong quá trình phân tích file.")

    finally:
        # Cleanup: Luôn luôn xóa file tạm dù thành công hay ném ra Exception
        if os.path.exists(safe_filename):
            os.remove(safe_filename)

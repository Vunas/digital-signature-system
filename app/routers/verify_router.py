from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import os
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

    temp_path = f"temp_{file.filename}"
    try:
        logger.info(
            f"User {current_user.username} đang thực hiện xac thực tài liệu PDF: {file.filename}"
        )
        file.file.seek(0)

        # Sử dụng aiofiles để lưu file bất đồng bộ (tránh block I/O)
        async with aiofiles.open(temp_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        # Xác thực file (Hệ thống tự log vào Audit)
        result = await verify_service.verify_pdf_signature(db, temp_path, current_user.id)

        await db.commit()  
        return result

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

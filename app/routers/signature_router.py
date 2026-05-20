from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.signature_schema import SignatureCreate, SignatureResponse
from app.services.sign_service import sign_service
from app.utils.logger import logger

router = APIRouter(prefix="/api/signatures", tags=["Signatures"])


@router.post("/sign-pdf", response_model=SignatureResponse)
async def sign_document(
    sign_data: SignatureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ký số lên tài liệu PDF bằng cách tương tác với hệ thống PKI nội bộ."""
    try:
        logger.info(
            f"User {current_user.username} đang thực hiện ký tài liệu ID {sign_data.document_id}"
        )

        signature_record = await sign_service.sign_pdf(db, current_user.id, sign_data)

        await db.commit()
        return signature_record

    except ValueError as ve:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        await db.rollback()
        logger.error(f"Lỗi ký tài liệu: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi ký tài liệu: {str(e)}",
        )

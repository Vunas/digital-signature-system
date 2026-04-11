from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.signature_schema import SignatureCreate, SignatureResponse
from app.services.sign_service import sign_service
from app.utils.logger import logger

router = APIRouter(prefix="/api/signatures", tags=["Signatures"])


@router.post("/sign-pdf", response_model=SignatureResponse)
def sign_document(
    sign_data: SignatureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ký số lên tài liệu PDF.
    - `document_id`: ID của PDF đã upload.
    - `key_id`: ID của khóa sẽ dùng để ký (Phải có chứng chỉ đi kèm).
    """
    try:
        logger.info(
            f"User {current_user.username} đang thực hiện ký tài liệu ID {sign_data.document_id}"
        )
        signature_record = sign_service.sign_pdf(db, current_user.id, sign_data)
        return signature_record
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Lỗi ký tài liệu: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi hệ thống khi ký tài liệu.",
        )

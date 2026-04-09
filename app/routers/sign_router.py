import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.signature_schema import SignatureCreate, SignatureResponse
from app.services.sign_service import sign_document

router = APIRouter(prefix="/sign", tags=["Digital Signature"])


class MockUser:
    id: int = 1


@router.post("/", response_model=SignatureResponse)
def create_signature(
    sign_in: SignatureCreate,
    db: Session = Depends(get_db),
    current_user=Depends(lambda: MockUser()),
):
    logging.info(f"User {current_user.id} is attempting to sign document {sign_in.document_id} using key {sign_in.key_id} db={db}")
    """
    Ký số lên văn bản đã được upload bằng khóa của người dùng.
    Yêu cầu Passphrase để giải mã Private Key.
    """
    signature = sign_document(
        db=db,
        user_id=current_user.id,
        document_id=sign_in.document_id,
        key_id=sign_in.key_id,
        passphrase=sign_in.passphrase,
        private_key=sign_in.private_key,
    )
    return signature

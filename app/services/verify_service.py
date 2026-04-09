import base64
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.document import Document
from app.models.signature import Signature
from app.core.crypto import verify_signature
from app.services.log_service import create_verify_log


def verify_document_signature(db: Session, document_id: int, signature_id: int) -> dict:
    """
    Xác thực tính toàn vẹn và nguồn gốc của văn bản.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    signature_record = db.query(Signature).filter(Signature.id == signature_id).first()

    if not document or not signature_record:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy văn bản hoặc chữ ký"
        )

    if signature_record.document_id != document.id:
        raise HTTPException(status_code=400, detail="Chữ ký không thuộc về văn bản này")

    # Lấy Public Key từ Database (thông qua relationship)
    public_key_pem = signature_record.key.public_key.encode("utf-8")
    signature_bytes = base64.b64decode(signature_record.signature)

    is_valid = verify_signature(document.file_hash, signature_bytes, public_key_pem)

    # Ghi log lịch sử xác thực
    message = (
        "Xác thực thành công. Dữ liệu toàn vẹn."
        if is_valid
        else "Xác thực thất bại. Dữ liệu có thể đã bị thay đổi."
    )
    create_verify_log(db, document.id, signature_record.id, is_valid, message)

    return {
        "is_valid": is_valid,
        "message": message,
        "document_name": document.file_name,
        "signer_username": signature_record.signer.username,
        "verified_at": signature_record.signed_at,
    }

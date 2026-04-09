import base64
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.document import Document
from app.models.key import Key
from app.models.signature import Signature
from app.core.encryption import decrypt_private_key
from app.core.crypto import sign_data
from app.core.config import settings
from app.services.log_service import create_audit_log


def sign_document(
    db: Session,
    user_id: int,
    document_id: int,
    key_id: int,
    passphrase: str = None,
    private_key: str = None,
) -> Signature:
    """
    Thực hiện ký điện tử lên document_hash.
    Hỗ trợ cả khóa Server (dùng passphrase / master token) và khóa Local (dùng raw private_key).
    """
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )
    key = db.query(Key).filter(Key.id == key_id, Key.user_id == user_id).first()

    if not document or not key:
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản hoặc khóa")

    try:
        private_key_pem = b""

        # 1. Xác định Private Key dựa trên Storage Type
        if key.storage_type == "local":
            if not private_key:
                raise HTTPException(
                    status_code=400, detail="Vui lòng cung cấp file Private Key (.pem)!"
                )
            private_key_pem = private_key.encode("utf-8")
        else:
            # Khóa lưu trên Server: Nếu trống Passphrase thì dùng Master Token
            actual_passphrase = passphrase if passphrase else settings.SERVER_MASTER_KEY
            private_key_pem = decrypt_private_key(
                key.private_key_encrypted, actual_passphrase
            )

        # 2. Thực hiện ký trên chuỗi Hash
        signature_bytes = sign_data(document.file_hash, private_key_pem)

        # 3. Mã hóa base64 chữ ký để lưu DB
        signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

        # 4. Lưu chữ ký vào DB
        new_signature = Signature(
            document_id=document.id,
            key_id=key.id,
            user_id=user_id,
            signature=signature_b64,
            hash_algorithm="SHA-256",
            signature_algorithm="RSA-PSS",
        )
        db.add(new_signature)
        db.commit()
        db.refresh(new_signature)

        # 5. Ghi Log Audit
        create_audit_log(
            db,
            user_id,
            "SIGN_DOCUMENT",
            f"Đã ký văn bản ID {document_id} bằng khóa ID {key_id} ({key.storage_type})",
        )

        return new_signature

    except ValueError as e:
        print(e)
        raise HTTPException(
            status_code=400,
            detail="Passphrase không chính xác hoặc File Private Key không hợp lệ!",
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi ký số: {str(e)}")

from sqlalchemy.orm import Session
from app.models.log import AuditLog
from app.models.verify_log import VerifyLog


def create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    description: str,
    ip_address: str = "127.0.0.1",
):
    """
    Ghi nhận mọi hành động của người dùng (Non-repudiation)
    """
    log_entry = AuditLog(
        user_id=user_id, action=action, description=description, ip_address=ip_address
    )
    db.add(log_entry)
    db.commit()
    return log_entry


def create_verify_log(
    db: Session, document_id: int, signature_id: int, is_valid: bool, message: str
):
    """
    Ghi nhận lịch sử xác thực chữ ký (Ăn điểm cực mạnh)
    """
    log_entry = VerifyLog(
        document_id=document_id,
        signature_id=signature_id,
        is_valid=is_valid,
        message=message,
    )
    db.add(log_entry)
    db.commit()
    return log_entry

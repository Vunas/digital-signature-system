from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.document_schema import DocumentResponse
from app.schemas.verify_schema import VerifyRequest, VerifyResponse
from app.services.file_service import process_and_save_document
from app.services.verify_service import verify_document_signature
from app.models.document import Document
from app.models.key import Key
from app.core.crypto import hash_file_content, verify_signature
import base64
import json

router = APIRouter(prefix="/documents", tags=["Documents & Verification"])


class MockUser:
    id: int = 1


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(lambda: MockUser()),
):
    document = process_and_save_document(db, file, current_user.id)
    return document


@router.post("/verify", response_model=VerifyResponse)
def verify_signature_endpoint(verify_in: VerifyRequest, db: Session = Depends(get_db)):
    result = verify_document_signature(
        db=db, document_id=verify_in.document_id, signature_id=verify_in.signature_id
    )
    return result


@router.post("/verify-file")
async def verify_file_offline(
    file: UploadFile = File(...),
    sig_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    CHUẨN LOGIC XÁC THỰC MỚI:
    1. Upload file PDF và file .sig.
    2. Đọc file .sig (JSON) để trích xuất 'key_id' và 'signature'.
    3. Lấy Public Key của người ký dựa trên 'key_id'.
    4. Đối chiếu chữ ký.
    """
    # 1. Đọc nội dung file .sig
    sig_content = await sig_file.read()
    try:
        # Cố gắng Parse JSON từ file
        sig_data = json.loads(sig_content)
        signature_base64 = sig_data.get("signature")
        key_id = sig_data.get("key_id")

        if not signature_base64 or not key_id:
            raise ValueError(
                "File chữ ký không đúng chuẩn. Thiếu 'signature' hoặc 'key_id'."
            )

    except json.JSONDecodeError:
        return {
            "is_valid": False,
            "message": "Lỗi: File .sig không đúng định dạng JSON.",
        }
    except Exception as e:
        return {"is_valid": False, "message": str(e)}

    # 2. Tìm khóa công khai trên hệ thống thông qua key_id
    key = db.query(Key).filter(Key.id == key_id).first()
    if not key:
        return {
            "is_valid": False,
            "message": "Không tìm thấy khóa công khai trên hệ thống (Khóa này có thể đã bị xóa).",
        }

    public_key_pem = key.public_key.encode("utf-8")

    # 3. Đọc và băm file PDF vừa upload
    content = await file.read()
    current_file_hash = hash_file_content(content)

    # 4. Giải mã và Xác thực
    try:
        signature_bytes = base64.b64decode(signature_base64)
        is_valid = verify_signature(current_file_hash, signature_bytes, public_key_pem)

        if is_valid:
            return {
                "is_valid": True,
                "message": f"File nguyên vẹn và được ký bởi tài khoản: {key.owner.username} (Bằng: {key.key_name}).",
            }
        else:
            return {
                "is_valid": False,
                "message": "Xác thực thất bại! File đã bị chỉnh sửa hoặc sai chữ ký.",
            }
    except Exception as e:
        return {
            "is_valid": False,
            "message": f"Chữ ký không đúng định dạng thuật toán. Chi tiết: {str(e)}",
        }


@router.get("/my-documents")
def get_my_documents(
    db: Session = Depends(get_db), current_user=Depends(lambda: MockUser())
):
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return docs

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.key import Key
from app.models.document import Document
from app.models.signature import Signature
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/dashboard-api", tags=["Dashboard"])


class MockUser:
    id: int = 1
    username: str = "admin"


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db), current_user=Depends(lambda: MockUser())
):
    """
    Trữ lượng API gộp: Trả về thống kê và toàn bộ danh sách (Keys, Docs, Signatures)
    để hiển thị trên Dashboard chỉ với 1 lần gọi.
    """
    # 1. Fetch Danh sách Khóa
    keys = (
        db.query(Key)
        .filter(Key.user_id == current_user.id)
        .order_by(Key.created_at.desc())
        .all()
    )

    # 2. Fetch Danh sách Tài liệu
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    # 3. Fetch Danh sách Chữ ký (Kèm theo thông tin liên kết)
    sigs = (
        db.query(Signature)
        .filter(Signature.user_id == current_user.id)
        .order_by(Signature.signed_at.desc())
        .all()
    )

    # Định dạng dữ liệu Keys
    keys_data = [
        {
            "id": k.id,
            "name": k.key_name,
            "algorithm": f"{k.algorithm}-{k.key_size}",
            "storage_type": k.storage_type,
            "public_key": k.public_key,
            "private_key_encrypted": k.private_key_encrypted,
            "created_at": k.created_at.strftime("%Y-%m-%d %H:%M"),
            "is_revoked": k.is_revoked,
        }
        for k in keys
    ]

    # Định dạng dữ liệu Documents
    docs_data = [
        {
            "id": d.id,
            "name": d.file_name,
            "hash": d.file_hash,
            "size": round(d.file_size / 1024, 2),  # KB
            "uploaded_at": d.uploaded_at.strftime("%Y-%m-%d %H:%M"),
        }
        for d in docs
    ]

    # Định dạng dữ liệu Signatures
    sigs_data = [
        {
            "id": s.id,
            "document_name": s.document.file_name if s.document else "N/A",
            "key_name": s.key.key_name if s.key else "N/A",
            "key_id": s.key_id,
            "signature_base64": s.signature,
            "algorithm": s.signature_algorithm,
            "signer": current_user.username,
            "signed_at": s.signed_at.strftime("%Y-%m-%d %H:%M"),
        }
        for s in sigs
    ]

    return {
        "stats": {
            "total_keys": len(keys),
            "total_docs": len(docs),
            "total_sigs": len(sigs),
        },
        "keys": keys_data,
        "documents": docs_data,
        "signatures": sigs_data,
    }


@router.get("/download-doc/{doc_id}")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    """API hỗ trợ tải file PDF gốc"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc or not os.path.exists(doc.file_path):
        return {"error": "File không tồn tại"}
    return FileResponse(
        path=doc.file_path, filename=doc.file_name, media_type=doc.mime_type
    )

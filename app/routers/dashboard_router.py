from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import base64

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.repositories.key_repo import key_repo
from app.repositories.document_repo import document_repo
from app.repositories.signature_repo import signature_repo

router = APIRouter(prefix="/dashboard-api", tags=["Dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    API cung cấp toàn bộ dữ liệu thống kê cho giao diện Dashboard HTML.
    """
    keys = await key_repo.get_all_by_user(db, current_user.id)
    docs = await document_repo.get_all_by_user(db, current_user.id)

    signatures_list = []
    for doc in docs:
        doc_sigs = await signature_repo.get_by_document(db, doc.id)
        for sig in doc_sigs:
            sig_base64 = (
                base64.b64encode(sig.signature_value).decode("utf-8")
                if sig.signature_value
                else "N/A"
            )

            key_name = "Khóa bị ẩn/xóa"
            key = await key_repo.get_by_id(db, sig.key_id, current_user.id)
            if key:
                key_name = key.key_name

            signatures_list.append(
                {
                    "id": sig.id,
                    "document_name": doc.file_name,
                    "key_id": sig.key_id,
                    "key_name": key_name,
                    "signer": sig.signer_name,
                    "algorithm": sig.signature_algorithm.value,
                    "signed_at": sig.created_at.strftime("%H:%M:%S %d-%m-%Y")
                    if sig.created_at
                    else "",
                    "signature_base64": sig_base64,
                }
            )

    return {
        "stats": {
            "total_keys": len(keys),
            "total_docs": len(docs),
            "total_sigs": len(signatures_list),
        },
        "keys": [
            {
                "id": k.id,
                "name": k.key_name,
                "algorithm": k.algorithm.value,
                "storage_type": k.storage_type.value,
                "created_at": k.created_at.strftime("%d-%m-%Y") if k.created_at else "",
                "public_key": k.public_key.decode("utf-8")
                if isinstance(k.public_key, bytes)
                else k.public_key,
                "private_key_encrypted": base64.b64encode(k.private_key_encrypted).decode("utf-8")
                if isinstance(k.private_key_encrypted, bytes)
                else "",
            }
            for k in keys
        ],
        "documents": [
            {
                "id": d.id,
                "name": d.file_name,
                "hash": d.file_hash,
                "size": round(d.file_size / 1024, 2) if d.file_size else 0,
            }
            for d in docs
        ],
        "signatures": signatures_list,
    }

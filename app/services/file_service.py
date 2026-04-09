import hashlib
import os
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.document import Document

UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def process_and_save_document(db: Session, file: UploadFile, user_id: int) -> Document:
    """
    Đọc file upload, tính mã băm SHA-256 và lưu thông tin vào Database.
    """
    content = file.file.read()

    # 1. Tính toán mã băm SHA-256 (Hash function)
    hasher = hashlib.sha256()
    hasher.update(content)
    file_hash = hasher.hexdigest()

    # 2. Lưu file vật lý (có thể bỏ qua nếu dùng Cloud hoặc Stateless)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # 3. Lưu thông tin vào Database
    new_doc = Document(
        user_id=user_id,
        file_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        file_hash=file_hash,
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return new_doc

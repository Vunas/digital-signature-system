import os
from fastapi import UploadFile
from sqlalchemy.orm import Session
import uuid

from app.utils.file_utils import save_upload_file
from app.utils.hash_utils import calculate_file_hash
from app.repositories.document_repo import document_repo


class FileService:
    async def upload_document(self, db: Session, user_id: int, file: UploadFile):
        """
        Xử lý upload file:
        1. Tạo tên file unique tránh trùng lặp
        2. Lưu xuống ổ cứng
        3. Tính toán mã băm SHA-256
        4. Lưu thông tin vào Database
        """
        # Tạo tên file an toàn với UUID
        safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"

        # Lưu file vật lý
        saved_path = await save_upload_file(file, safe_filename)

        # Lấy kích thước và tính Hash
        file_size = os.path.getsize(saved_path)
        file_hash = calculate_file_hash(saved_path)

        # Lưu vào Database thông qua Repository
        doc = document_repo.create(
            db=db,
            user_id=user_id,
            file_name=file.filename,
            original_file_path=saved_path,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=file.content_type,
        )
        return doc


file_service = FileService()

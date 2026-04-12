import uuid
import hashlib
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.utils.file_utils import save_file
from app.repositories.document_repo import document_repo


class FileService:
    async def upload_document(self, db: Session, user_id: int, file: UploadFile):
        """
        Xử lý upload file: Tự động Fallback Local nếu cần.
        """
        # Đọc dữ liệu file thành dạng byte
        content = await file.read()

        # Tạo tên file an toàn
        safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"

        # Tính kích thước và Hash
        file_size = len(content)
        file_hash = hashlib.sha256(content).hexdigest()

        # Gọi hàm save_file thông minh (Tự nhận biết Cloud/Local)
        saved_path = await save_file(
            content=content, filename=safe_filename, content_type=file.content_type
        )

        # Lưu vào Database
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

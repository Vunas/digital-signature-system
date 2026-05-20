import uuid
import hashlib
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.file_utils import save_file
from app.repositories.document_repo import document_repo

# Centralized Enums
from app.models.enums import TargetResourceType
from app.services.log_service import log_service


class FileService:
    async def upload_document(self, db: AsyncSession, user_id: int, file: UploadFile):
        content = await file.read()
        safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"

        file_size = len(content)
        file_hash = hashlib.sha256(content).hexdigest()

        saved_path = await save_file(
            content=content, filename=safe_filename, content_type=file.content_type
        )

        doc = await document_repo.create(
            db=db,
            user_id=user_id,
            file_name=file.filename,
            original_file_path=saved_path,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=file.content_type,
        )

        await log_service.log_action(
            db=db,
            user_id=user_id,
            action="UPLOAD_DOCUMENT",
            target_type=TargetResourceType.DOCUMENT,
            target_id=str(doc.id),
            payload={"file_name": file.filename, "file_hash": file_hash},
        )

        return doc


file_service = FileService()

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document, DocumentStatus


class DocumentRepository:
    async def get_by_id(self, db: AsyncSession, doc_id: int, user_id: int):
        stmt = select(Document).where(Document.id == doc_id, Document.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_user(self, db: AsyncSession, user_id: int):
        stmt = (
            select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, **kwargs):
        db_obj = Document(**kwargs)
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def update_status(
        self,
        db: AsyncSession,
        db_obj: Document,
        status: DocumentStatus,
        signed_path: str = None,
        signed_hash: str = None,
    ):
        db_obj.status = status
        if signed_path:
            db_obj.signed_file_path = signed_path
        if signed_hash:
            db_obj.signed_file_hash = signed_hash

        await db.flush()
        return db_obj


document_repo = DocumentRepository()

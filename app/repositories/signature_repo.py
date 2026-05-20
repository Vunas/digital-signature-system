from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.signature import Signature


class SignatureRepository:
    async def get_by_document(self, db: AsyncSession, document_id: int):
        stmt = select(Signature).where(Signature.document_id == document_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, **kwargs):
        db_obj = Signature(**kwargs)
        db.add(db_obj)
        await db.flush()  
        await db.refresh(db_obj)
        return db_obj


signature_repo = SignatureRepository()

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.certificate import Certificate


class CertificateRepository:
    async def get_by_id(self, db: AsyncSession, cert_id: int):
        stmt = select(Certificate).where(Certificate.id == cert_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_key_id(self, db: AsyncSession, key_id: int):
        stmt = select(Certificate).where(Certificate.key_id == key_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str):
        stmt = select(Certificate).where(Certificate.cert_name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, **kwargs):
        db_obj = Certificate(**kwargs)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


certificate_repo = CertificateRepository()

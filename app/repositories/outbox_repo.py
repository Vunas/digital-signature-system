from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, UTC

from app.models.outbox_event import OutboxEvent, OutboxStatus
from app.schemas.outbox_schema import OutboxEventCreate


class OutboxRepository:
    async def create(self, db: AsyncSession, obj_in: OutboxEventCreate):
        db_obj = OutboxEvent(
            aggregate_type=obj_in.aggregate_type,
            aggregate_id=obj_in.aggregate_id,
            event_type=obj_in.event_type,
            payload=obj_in.payload,
            status=OutboxStatus.PENDING
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def get_pending_events(self, db: AsyncSession, limit: int = 50):
        """Lấy danh sách các sự kiện đang chờ xử lý."""
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PENDING)
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def mark_as_processed(self, db: AsyncSession, event: OutboxEvent):
        """Đánh dấu sự kiện đã được xử lý thành công."""
        event.status = OutboxStatus.PROCESSED
        event.processed_at = datetime.now(UTC)
        await db.flush()
        return event

    async def mark_as_failed(self, db: AsyncSession, event: OutboxEvent, error_msg: str):
        """Đánh dấu sự kiện bị lỗi để sau này Retry."""
        event.status = OutboxStatus.FAILED
        event.error_message = error_msg
        event.processed_at = datetime.now(UTC)
        await db.flush()
        return event


outbox_repo = OutboxRepository()
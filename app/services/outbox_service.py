from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox_event import OutboxEvent
from app.models.enums import OutboxStatus
from app.repositories.outbox_repo import outbox_repo
from app.utils.logger import logger
from app.db.session import AsyncSessionLocal


class OutboxService:
    async def publish_event(
        self,
        db: AsyncSession,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict,
    ) -> OutboxEvent:
        new_event = OutboxEvent(
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            event_type=event_type,
            payload=payload,
            status=OutboxStatus.PENDING,
        )
        db.add(new_event)
        await db.flush()

        logger.info(f"Đã tạo Outbox Event: {event_type} cho {aggregate_type} ID: {aggregate_id}")
        return new_event

    async def process_event(self, event: OutboxEvent):
        logger.info(
            f"Đang xử lý Event: {event.event_type} cho {event.aggregate_type} ID: {event.aggregate_id}"
        )
        if event.event_type == "CERTIFICATE_CREATED":
            pass
        elif event.event_type == "USER_REGISTERED":
            pass

    async def run_worker(self):
        async with AsyncSessionLocal() as db:
            try:
                pending_events = await outbox_repo.get_pending_events(db, limit=100)

                if not pending_events:
                    return

                logger.info(f"Tìm thấy {len(pending_events)} Outbox Events cần xử lý.")

                for event in pending_events:
                    try:
                        await self.process_event(event)
                        event.mark_processed()
                    except Exception as e:
                        logger.error(f"Lỗi khi xử lý Outbox Event ID {event.id}: {str(e)}")
                        event.mark_failed(str(e))

                await db.commit()

            except Exception as e:
                await db.rollback()
                logger.error(f"Lỗi Outbox Worker: {str(e)}")


outbox_service = OutboxService()

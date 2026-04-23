from app.repositories.outbox_repo import outbox_repo
from app.utils.logger import logger
from app.db.session import AsyncSessionLocal


class OutboxService:
    async def process_event(self, event):
        """
        Nơi định nghĩa logic để xử lý sự kiện.
        Tích hợp RabbitMQ/Kafka, hoặc gửi Email, gọi API bên thứ 3 ở đây.
        """
        logger.info(
            f"Đang xử lý Event: {event.event_type} cho {event.aggregate_type} ID: {event.aggregate_id}"
        )

        # Ví dụ giả lập:
        if event.event_type == "CERTIFICATE_CREATED":
            # await email_service.send_cert_created_email(event.payload["email"])
            pass
        elif event.event_type == "USER_REGISTERED":
            # await queue_service.publish("user_queue", event.payload)
            pass

    async def run_worker(self):
        """
        Worker chạy ngầm, liên tục quét bảng Outbox để xử lý.
        Bạn có thể đưa hàm này vào vòng lặp của FastAPI Lifespan hoặc chạy bằng Celery/Cronjob.
        """
        # Tạo một session riêng biệt cho Worker (không dính dáng đến Request Session)
        async with AsyncSessionLocal() as db:
            try:
                # 1. Lấy danh sách sự kiện đang PENDING
                pending_events = await outbox_repo.get_pending_events(db, limit=100)

                if not pending_events:
                    return

                logger.info(f"Tìm thấy {len(pending_events)} Outbox Events cần xử lý.")

                # 2. Xử lý từng sự kiện
                for event in pending_events:
                    try:
                        await self.process_event(event)
                        # Thành công -> Cập nhật trạng thái
                        await outbox_repo.mark_as_processed(db, event)
                    except Exception as e:
                        logger.error(f"Lỗi khi xử lý Outbox Event ID {event.id}: {str(e)}")
                        # Thất bại -> Ghi nhận lỗi để fix/retry
                        await outbox_repo.mark_as_failed(db, event, str(e))

                # 3. Chốt transaction cho toàn bộ batch event vừa xử lý
                await db.commit()

            except Exception as e:
                await db.rollback()
                logger.error(f"Lỗi Outbox Worker: {str(e)}")


outbox_service = OutboxService()

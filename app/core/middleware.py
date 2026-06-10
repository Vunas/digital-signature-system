from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
from app.utils.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Chặn (Intercept) mọi request đi vào và response đi ra khỏi hệ thống.
    Đo lường thời gian xử lý và ghi log giám sát.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Ghi nhận thông tin Request đầu vào
        client_ip = request.client.host if request.client else "Unknown"
        method = request.method
        url = request.url.path

        logger.info(f"📥 Incoming: {method} {url} - IP: {client_ip}")

        try:
            # Chuyển request cho ứng dụng xử lý
            response = await call_next(request)

            # Tính toán thời gian xử lý
            process_time = (time.time() - start_time) * 1000  # đổi ra mili-giây

            # Ghi nhận kết quả trả về
            logger.info(
                f"📤 Outgoing: {method} {url} - Status: {response.status_code} - Time: {process_time:.2f}ms"
            )

            # Trả thêm header X-Process-Time cho Client biết
            response.headers["X-Process-Time"] = str(process_time)
            return response

        except Exception as e:
            # Bắt lỗi nghiêm trọng (500 Internal Server Error)
            logger.error(f"❌ ERROR: {method} {url} - Exception: {str(e)}")
            raise e


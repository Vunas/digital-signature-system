import os
import aiofiles
from datetime import datetime
from pathlib import Path
from supabase import create_client, Client
from app.core.config import settings
import logging

BUCKET_NAME = "documents"
# Kiểm tra xem có cấu hình Supabase hợp lệ không
USE_SUPABASE = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)
supabase: Client = None

if USE_SUPABASE:
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        logging.error(f"Lỗi khởi tạo Supabase: {e}. Fallback về Local Storage.")
        USE_SUPABASE = False

# Thư mục lưu trữ Local (dùng khi Fallback)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
SIGNED_DIR = BASE_DIR / "storage" / "signed"

# Tạo sẵn thư mục Local nếu chưa có
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SIGNED_DIR, exist_ok=True)


async def save_file(
    content: bytes, filename: str, content_type: str = "application/pdf"
) -> str:
    """
    Tự động quyết định lưu file lên Supabase hay lưu xuống Ổ cứng Local.
    """
    if USE_SUPABASE:
        try:
            cloud_path = f"uploads/{filename}"
            supabase.storage.from_(BUCKET_NAME).upload(
                path=cloud_path,
                file=content,
                file_options={"content-type": content_type},
            )
            return cloud_path  # Trả về đường dẫn Cloud
        except Exception as e:
            logging.error(
                f"Supabase Upload lỗi: {e}. Fallback lưu file '{filename}' xuống Local."
            )
            # Chuyển tiếp xuống luồng ghi Local bên dưới

    # Luồng Local Storage (Chạy khi ko có cấu hình Supabase hoặc Upload Supabase thất bại)
    local_path = UPLOAD_DIR / filename
    async with aiofiles.open(local_path, "wb") as out_file:
        await out_file.write(content)

    # Ký hiệu tiền tố "local:" để phân biệt với đường dẫn Cloud trong DB
    return f"local:{str(local_path)}"


def get_signed_file_path(original_file_name: str, original_db_path: str) -> str:
    """
    Tạo đường dẫn file đã ký (Cloud hoặc Local tùy theo file gốc).
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_file_name)
    new_filename = f"signed_{name}_{timestamp_str}{ext}"

    if original_db_path.startswith("local:"):
        # Trả về đường dẫn Local
        return f"local:{str(SIGNED_DIR / new_filename)}"
    else:
        # Trả về đường dẫn Supabase
        return f"signed/{new_filename}"


def get_file_content(db_path: str) -> bytes:
    """
    Hàm tiện ích kéo nội dung file (Bytes) từ Local hoặc Cloud.
    Sử dụng trong Router Download và Sign_Service.
    """
    if db_path.startswith("local:"):
        real_path = db_path.replace("local:", "")
        with open(real_path, "rb") as f:
            return f.read()
    else:
        if USE_SUPABASE:
            return supabase.storage.from_(BUCKET_NAME).download(db_path)
        else:
            raise Exception(
                "Hệ thống mất kết nối Supabase, không thể tải file trên Cloud."
            )


def save_signed_file_content(
    db_path: str, content: bytes, content_type: str = "application/pdf"
):
    """
    Hàm đẩy nội dung file đã ký lên Cloud hoặc lưu đè xuống Local
    """
    if db_path.startswith("local:"):
        real_path = db_path.replace("local:", "")
        with open(real_path, "wb") as f:
            f.write(content)
    else:
        if USE_SUPABASE:
            supabase.storage.from_(BUCKET_NAME).upload(
                path=db_path, file=content, file_options={"content-type": content_type}
            )
        else:
            raise Exception(
                "Hệ thống mất kết nối Supabase, không thể upload file ký lên Cloud."
            )

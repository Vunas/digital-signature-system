import os
import aiofiles
from fastapi import UploadFile
from pathlib import Path
from datetime import datetime

# Thư mục lưu trữ file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
SIGNED_DIR = BASE_DIR / "storage" / "signed"

# Khởi tạo thư mục nếu chưa tồn tại
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SIGNED_DIR, exist_ok=True)


async def save_upload_file(upload_file: UploadFile, filename: str) -> str:
    """
    Lưu file PDF upload từ client xuống server an toàn bằng aiofiles (Async).
    """
    file_path = UPLOAD_DIR / filename
    async with aiofiles.open(file_path, "wb") as out_file:
        while content := await upload_file.read(1024 * 1024):  # Đọc từng chunk 1MB
            await out_file.write(content)
    return str(file_path)


def get_signed_file_path(original_filename: str) -> str:
    """
    Trả về đường dẫn lưu file sau khi ký, đảm bảo tính duy nhất.
    Ví dụ: hop_dong.pdf -> signed_hop_dong_20260410_214530.pdf
    """
    # Lấy thời gian hiện tại định dạng YYYYMMDD_HHMMSS
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Tách tên file và phần mở rộng (.pdf)
    name, ext = os.path.splitext(original_filename)

    # Tạo tên file mới
    new_filename = f"signed_{name}_{timestamp_str}{ext}"

    return str(SIGNED_DIR / new_filename)

import os


def format_file_size(size_in_bytes: int) -> str:
    """Đổi kích thước byte sang KB, MB để hiển thị lên UI cho đẹp."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"


def is_valid_pdf(filename: str, mime_type: str) -> bool:
    """Bảo mật: Chỉ cho phép upload file PDF."""
    allowed_extensions = {".pdf"}
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions and mime_type == "application/pdf"

import hashlib
import uuid


def generate_uuid() -> str:
    """Tạo chuỗi ngẫu nhiên duy nhất."""
    return str(uuid.uuid4())


def hash_text(text: str) -> str:
    """Băm một đoạn text bất kỳ (không phải file)"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

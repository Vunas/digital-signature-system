from cryptography.fernet import Fernet
from .config import settings

# Fernet sử dụng AES-128 trong chế độ CBC
cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt_private_key(private_key_bytes: bytes) -> bytes:
    """
    Mã hóa Private Key trước khi lưu vào Database (cột private_key_encrypted).
    Giải pháp an toàn cho việc lưu trữ 'server' storage_type.
    """
    return cipher_suite.encrypt(private_key_bytes)


def decrypt_private_key(encrypted_private_key: bytes) -> bytes:
    """
    Giải mã Private Key từ Database để sử dụng cho quá trình ký PDF.
    """
    return cipher_suite.decrypt(encrypted_private_key)

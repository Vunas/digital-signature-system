import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings


def _derive_key_from_passphrase(passphrase: str) -> bytes:
    """
    🔥 ĐÂY LÀ PHẦN ĂN ĐIỂM:
    Biến mật khẩu (passphrase) của người dùng thành một chìa khóa AES 256-bit an toàn
    bằng thuật toán Key Derivation Function (PBKDF2).
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=settings.ENCRYPTION_SALT.encode(),
        iterations=480000,  # Số vòng lặp cực cao, chống brute-force
    )
    # Tạo ra chìa khóa base64 dùng cho thuật toán Fernet (AES)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def encrypt_private_key(private_key_pem: bytes, passphrase: str) -> str:
    """
    Mã hóa Private Key bằng mật khẩu của người dùng trước khi lưu vào DB.
    Nếu Hacker lấy được DB, họ chỉ thấy các ký tự rác (Encrypted blob).
    """
    aes_key = _derive_key_from_passphrase(passphrase)
    f = Fernet(aes_key)
    encrypted_data = f.encrypt(private_key_pem)
    return encrypted_data.decode("utf-8")


def decrypt_private_key(encrypted_private_key: str, passphrase: str) -> bytes:
    """
    Giải mã Private Key trên RAM khi người dùng cần Ký văn bản.
    Nhập sai Passphrase -> Báo lỗi InvalidToken.
    """
    aes_key = _derive_key_from_passphrase(passphrase)
    f = Fernet(aes_key)
    try:
        decrypted_data = f.decrypt(encrypted_private_key.encode("utf-8"))
        return decrypted_data
    except Exception as e:
        print(e)
        raise ValueError("Passphrase không chính xác hoặc khóa đã bị hỏng!")

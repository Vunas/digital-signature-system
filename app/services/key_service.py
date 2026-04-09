from sqlalchemy.orm import Session
from app.models.key import Key
from app.core.crypto import generate_rsa_keypair
from app.core.encryption import encrypt_private_key
from app.core.config import settings
from typing import Tuple, Optional


def create_user_keypair(
    db: Session,
    user_id: int,
    key_name: str,
    storage_type: str,
    passphrase: Optional[str] = None,
    key_size: int = 2048,
) -> Tuple[Key, Optional[str]]:
    """
    Sinh cặp khóa RSA.
    - Nếu local: Không lưu DB, trả raw_private_key về để tải.
    - Nếu server: Mã hóa bằng Passphrase (hoặc Server Token nếu trống) rồi lưu DB.
    """
    # 1. Sinh cặp khóa RSA
    private_pem, public_pem = generate_rsa_keypair(key_size=key_size)

    encrypted_private = None
    raw_private_to_return = None

    # 2. Xử lý theo loại lưu trữ
    if storage_type == "local":
        # KHÔNG mã hóa, KHÔNG lưu DB. Chuẩn bị trả về dạng chuỗi cho Frontend tải file.
        raw_private_to_return = private_pem.decode("utf-8")
    else:
        # Lưu Server
        # Nếu user không nhập passphrase, dùng Server Master Key
        actual_passphrase = passphrase if passphrase else settings.SERVER_MASTER_KEY
        encrypted_private = encrypt_private_key(private_pem, actual_passphrase)

    # 3. Lưu vào DB
    new_key = Key(
        user_id=user_id,
        key_name=key_name,
        public_key=public_pem.decode("utf-8"),
        private_key_encrypted=encrypted_private,  # Sẽ là None nếu lưu local
        storage_type=storage_type,
        key_size=key_size,
        algorithm="RSA",
    )

    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    return new_key, raw_private_to_return

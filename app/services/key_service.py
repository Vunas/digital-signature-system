from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import hashlib

from app.schemas.key_schema import KeyCreate
from app.repositories.key_repo import key_repo
from app.services.crypto.aes_service import aes_service
from app.models.key import KeyStorageType


class KeyService:
    def create_key(self, db: Session, user_id: int, key_data: KeyCreate):
        # 1. Sinh cặp khóa RSA
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=key_data.key_size
        )

        # Xuất Private Key gốc (không mã hóa) để dùng cho Local hoặc Auto Server
        unencrypted_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        encrypted_priv_pem = b""
        raw_private_key_to_return = None

        # 2. Xử lý Logic 3 trường hợp lưu trữ
        if (
            key_data.storage_type == "local"
            or key_data.storage_type == KeyStorageType.local
        ):
            # KIỂU 3: LOCAL - Không lưu Private Key vào DB, trả về cho người dùng tải
            raw_private_key_to_return = unencrypted_pem.decode("utf-8")
            encrypted_priv_pem = b""

        else:  # SERVER
            if key_data.passphrase:
                # KIỂU 2: SERVER ZERO-KNOWLEDGE - Mã hóa bằng Passphrase của User
                encrypted_priv_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.BestAvailableEncryption(
                        key_data.passphrase.encode("utf-8")
                    ),
                )
            else:
                # KIỂU 1: SERVER AUTO - Mã hóa bằng AES Master Key của hệ thống
                encrypted_priv_pem = aes_service.encrypt_key(unencrypted_pem)

        # 3. Xuất Public Key và tính Fingerprint
        pub_key_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        fingerprint = hashlib.sha256(pub_key_pem).hexdigest()[:16].upper()

        # 4. Lưu Database
        db_key = key_repo.create(
            db=db,
            user_id=user_id,
            key_name=key_data.key_name,
            public_key=pub_key_pem,
            private_key_encrypted=encrypted_priv_pem,
            key_size=key_data.key_size,
            algorithm=key_data.algorithm,
            storage_type=key_data.storage_type,
            key_fingerprint=fingerprint,
        )

        # Đính kèm raw_private_key vào object response (chỉ có giá trị nếu là Local)
        setattr(db_key, "raw_private_key", raw_private_key_to_return)

        return db_key


key_service = KeyService()

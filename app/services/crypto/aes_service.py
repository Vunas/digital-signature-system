from app.core.encryption import encrypt_private_key, decrypt_private_key


class AESService:
    """
    Wrapper Service cho phần mã hóa Private Key bằng AES.
    Giúp tầng Business Logic không bị phụ thuộc trực tiếp vào tầng Core.
    """

    @staticmethod
    def encrypt_key(plain_private_key: bytes) -> bytes:
        return encrypt_private_key(plain_private_key)

    @staticmethod
    def decrypt_key(encrypted_private_key: bytes) -> bytes:
        return decrypt_private_key(encrypted_private_key)


# Khởi tạo instance aes_service
aes_service = AESService()

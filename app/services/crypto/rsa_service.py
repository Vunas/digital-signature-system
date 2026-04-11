from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class RSAService:
    @staticmethod
    def generate_key_pair(key_size: int = 2048) -> tuple[bytes, bytes]:
        """
        Sinh cặp khóa RSA (Public Key & Private Key).
        Trả về dưới định dạng PEM (bytes).
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

        public_key = private_key.public_key()

        # Xuất Private Key ra định dạng PEM (Không có mật khẩu bảo vệ ở mức file vì ta sẽ mã hóa AES khi lưu DB)
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Xuất Public Key ra định dạng PEM
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return pem_public, pem_private


# Khởi tạo instance rsa_service để các file khác (như key_service.py) có thể import và sử dụng trực tiếp
rsa_service = RSAService()

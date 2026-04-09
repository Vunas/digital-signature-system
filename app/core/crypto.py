import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature


def hash_file_content(file_bytes: bytes) -> str:
    """
    Hàm Băm (Hash Function): Băm dữ liệu đầu vào thành chuỗi cố định SHA-256.
    Đảm bảo tính vẹn toàn (Integrity). Một byte thay đổi, mã băm sẽ khác hoàn toàn.
    """
    hasher = hashlib.sha256()
    hasher.update(file_bytes)
    return hasher.hexdigest()


def generate_rsa_keypair(key_size: int = 2048) -> tuple[bytes, bytes]:
    """
    Tạo cặp khóa RSA (Công khai và Bí mật). Khuyến nghị chuẩn hiện tại là 2048 hoặc 4096 bit.
    Trả về định dạng PEM để dễ dàng lưu trữ và chia sẻ.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )

    # Chuyển Private Key sang dạng bytes (PEM)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),  # Sẽ được mã hóa AES ở core/encryption.py
    )

    # Chuyển Public Key sang dạng bytes (PEM)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return private_pem, public_pem


def sign_data(file_hash: str, private_key_pem: bytes) -> bytes:
    """
    Ký số: Sử dụng Khóa bí mật (Private Key) để mã hóa giá trị băm của văn bản.
    Sử dụng chuẩn padding PSS mạnh mẽ hơn chuẩn PKCS1v1.5 cũ.
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None,  # Đã giải mã bằng AES ở ngoài
    )

    signature = private_key.sign(
        file_hash.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    return signature


def verify_signature(file_hash: str, signature: bytes, public_key_pem: bytes) -> bool:
    """
    Xác minh: Sử dụng Khóa công khai (Public Key) để giải mã chữ ký,
    so sánh với mã băm thực tế của file.
    """
    public_key = serialization.load_pem_public_key(public_key_pem)

    try:
        public_key.verify(
            signature,
            file_hash.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        return True  # Trùng khớp -> Hợp lệ
    except InvalidSignature:
        return False  # Không khớp -> Bị chỉnh sửa hoặc sai chữ ký

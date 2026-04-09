from passlib.context import CryptContext

# Khởi tạo ngữ cảnh băm mật khẩu, sử dụng thuật toán bcrypt mạnh mẽ
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu người dùng nhập vào có khớp với mã băm trong DB không.
    Tuyệt đối không so sánh chuỗi trực tiếp.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Băm mật khẩu người dùng trước khi lưu vào Database.
    Thuật toán bcrypt tự động sinh ra Salt ngẫu nhiên cho mỗi lần băm,
    chống lại các cuộc tấn công Rainbow Table.
    """
    return pwd_context.hash(password)

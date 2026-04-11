import hashlib


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Tính toán mã băm (Hash) của một tệp tin.
    Đọc theo từng chunk để không làm tràn RAM với các file PDF lớn.
    """
    hash_func = hashlib.new(algorithm.lower().replace("-", ""))

    with open(file_path, "rb") as f:
        # Đọc mỗi lần 4KB
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def calculate_data_hash(data: bytes, algorithm: str = "sha256") -> str:
    """Tính mã băm cho dữ liệu thô (bytes)."""
    hash_func = hashlib.new(algorithm.lower().replace("-", ""))
    hash_func.update(data)
    return hash_func.hexdigest()

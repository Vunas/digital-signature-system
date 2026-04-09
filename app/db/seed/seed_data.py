import sys
import os
from sqlalchemy.orm import Session
import hashlib
import base64
from app.db.database import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.key import Key
from app.models.document import Document
from app.models.signature import Signature
from app.core.security import get_password_hash
from app.core.crypto import generate_rsa_keypair, sign_data
from app.core.encryption import encrypt_private_key
from app.services.log_service import create_audit_log

# Đảm bảo có thể import các module từ thư mục app khi chạy script này độc lập
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def seed_db():
    print("🌱 Bắt đầu tạo dữ liệu mẫu (Seed Data)...")
    db: Session = SessionLocal()

    try:
        # 1. TẠO BẢNG NẾU CHƯA CÓ
        Base.metadata.create_all(bind=engine)

        # 2. KIỂM TRA XEM ĐÃ CÓ DỮ LIỆU CHƯA
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("⚠️ Dữ liệu mẫu đã tồn tại. Bỏ qua quá trình Seed.")
            return

        # ==========================================
        # BƯỚC 1: TẠO NGƯỜI DÙNG (USER)
        # ==========================================
        print("👤 Đang tạo User mẫu...")
        # Mật khẩu đăng nhập là: 123456
        user1 = User(
            username="admin",
            password_hash=get_password_hash("123456"),
            is_active=True,
        )
        db.add(user1)
        db.commit()
        db.refresh(user1)
        print(f"  -> Đã tạo user: {user1.username} (Mật khẩu: 123456)")

        # ==========================================
        # BƯỚC 2: TẠO CẶP KHÓA (RSA KEYS)
        # ==========================================
        print("🔑 Đang tạo các khóa RSA 2048-bit (sẽ mất vài giây)...")

        # Khóa 1: Lưu trên Server (Có passphrase)
        passphrase = "secret_passphrase"
        private_pem_server, public_pem_server = generate_rsa_keypair(key_size=2048)
        encrypted_private = encrypt_private_key(private_pem_server, passphrase)

        key_server = Key(
            user_id=user1.id,
            key_name="Khóa Giám Đốc 2026 (Server)",
            public_key=public_pem_server.decode("utf-8"),
            private_key_encrypted=encrypted_private,
            storage_type="server",  # <-- Đã thêm thuộc tính mới
            key_size=2048,
            algorithm="RSA",
        )
        db.add(key_server)

        # Khóa 2: Lưu Local (Trống Private Key trên DB)
        private_pem_local, public_pem_local = generate_rsa_keypair(key_size=2048)
        key_local = Key(
            user_id=user1.id,
            key_name="Khóa Cá Nhân (Local)",
            public_key=public_pem_local.decode("utf-8"),
            private_key_encrypted=None,  # <-- Để trống theo logic lưu Local
            storage_type="local",  # <-- Đã thêm thuộc tính mới
            key_size=2048,
            algorithm="RSA",
        )
        db.add(key_local)

        db.commit()
        db.refresh(key_server)
        db.refresh(key_local)
        print(f"  -> Đã tạo khóa 1: {key_server.key_name} (Passphrase: {passphrase})")
        print(f"  -> Đã tạo khóa 2: {key_local.key_name} (Local - Không lưu DB)")

        # ==========================================
        # BƯỚC 3: TẠO VĂN BẢN MẪU (DOCUMENT)
        # ==========================================
        print("📄 Đang tạo dữ liệu Văn bản mẫu...")
        dummy_content = (
            b"Day la noi dung cua hop dong kinh te cuc ky quan trong nam 2026."
        )
        file_hash = hashlib.sha256(dummy_content).hexdigest()

        doc1 = Document(
            user_id=user1.id,
            file_name="Hop_Dong_Kinh_Te_2026.pdf",
            file_path="uploads/documents/Hop_Dong_Kinh_Te_2026.pdf",
            file_size=len(dummy_content),
            mime_type="application/pdf",
            file_hash=file_hash,
        )
        db.add(doc1)
        db.commit()
        db.refresh(doc1)
        print(
            f"  -> Đã tạo tài liệu: {doc1.file_name} (Hash: {doc1.file_hash[:15]}...)"
        )

        # Tạo file vật lý giả lập trong thư mục uploads
        os.makedirs("uploads/documents", exist_ok=True)
        with open(doc1.file_path, "wb") as f:
            f.write(dummy_content)

        # ==========================================
        # BƯỚC 4: TẠO CHỮ KÝ MẪU (SIGNATURE)
        # ==========================================
        print("✍️ Đang thực hiện ký số lên văn bản bằng Khóa Server...")
        # Lấy file hash và ký bằng private_pem_server
        signature_bytes = sign_data(doc1.file_hash, private_pem_server)
        signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

        sig1 = Signature(
            document_id=doc1.id,
            key_id=key_server.id,
            user_id=user1.id,
            signature=signature_b64,
            hash_algorithm="SHA-256",
            signature_algorithm="RSA-PSS",
        )
        db.add(sig1)
        db.commit()
        db.refresh(sig1)
        print("  -> Đã tạo chữ ký số thành công.")

        # ==========================================
        # BƯỚC 5: GHI LOG HỆ THỐNG
        # ==========================================
        create_audit_log(
            db, user1.id, "SEED_DATA", "Hệ thống tự động khởi tạo dữ liệu mẫu"
        )

        print("✅ Hoàn thành Seed Data! Hệ thống đã sẵn sàng để Demo.")
        print("-" * 40)
        print("🚀 THÔNG TIN ĐĂNG NHẬP DEMO:")
        print("Tài khoản : admin")
        print("Mật khẩu  : 123456")
        print(f"Passphrase: {passphrase} (Dành cho Khóa Server)")
        print("-" * 40)

    except Exception as e:
        print(f"❌ Lỗi trong quá trình tạo dữ liệu mẫu: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()

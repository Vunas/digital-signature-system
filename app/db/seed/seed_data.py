import sys
import os
import hashlib

from app.db.session import SessionLocal, engine
from app.db.base import Base

# IMPORT ĐẦY ĐỦ MODELS
from app.models.user import User
from app.models.document import Document
from app.models.certificate import CertType, CertificateChain

from app.core.security import get_password_hash
from app.schemas.key_schema import KeyCreate
from app.schemas.certificate_schema import CertificateCreate
from app.services.key_service import key_service
from app.services.certificate_service import certificate_service

# Thêm đường dẫn root để import các module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def seed_db(force=False):
    print("🌱 Bắt đầu tạo dữ liệu mẫu (Seed Data)...")
    db = SessionLocal()

    try:
        # 1. TẠO BẢNG NẾU CHƯA CÓ
        Base.metadata.create_all(bind=engine)

        # 2. KIỂM TRA XEM ĐÃ CÓ DỮ LIỆU CHƯA
        admin = db.query(User).filter(User.username == "admin").first()
        if admin and not force:
            print("⚠️ Dữ liệu mẫu đã tồn tại. Bỏ qua quá trình Seed.")
            return

        if force:
            print("♻️ Refresh Seed: Xoá dữ liệu cũ...")
            db.query(CertificateChain).delete()
            db.query(Document).delete()
            db.query(User).delete()
            db.commit()

        # ==========================================
        # BƯỚC 1: TẠO NGƯỜI DÙNG (USER)
        # ==========================================
        print("👤 Đang tạo User mẫu...")
        user1 = User(
            username="admin",
            password_hash=get_password_hash("123456"),
            is_active=True,
        )
        db.add(user1)
        db.commit()
        db.refresh(user1)
        print(f"  -> Đã tạo user: {user1.username} (Mật khẩu: 123456)")

        # BƯỚC 2: TẠO ROOT CA
        print("🔑 Tạo Root CA...")
        root_key = key_service.create_key(
            db, user1.id, KeyCreate(key_name="Root CA Key", key_size=2048)
        )
        root_cert_data = CertificateCreate(
            cert_name="SecureSign Root CA",
            key_id=root_key.id,
            issuer="SecureSign Root CA",
            subject="SecureSign Root CA",
            valid_days=3650,
            cert_type=CertType.ROOT,
        )
        root_cert = certificate_service.create_root_ca(db, user1.id, root_cert_data)
        db.add(
            CertificateChain(
                certificate_id=root_cert.id,
                ca_certificate_data=root_cert.certificate_data,
                level=0,
            )
        )
        db.commit()
        print("  -> Đã tạo Root CA")

        # BƯỚC 3: TẠO INTERMEDIATE CA
        print("🔑 Tạo Intermediate CA...")
        inter_key = key_service.create_key(
            db, user1.id, KeyCreate(key_name="Intermediate CA Key", key_size=2048)
        )
        inter_cert_data = CertificateCreate(
            cert_name="SecureSign Intermediate CA",
            key_id=inter_key.id,
            issuer="SecureSign Root CA",
            subject="SecureSign Intermediate CA",
            valid_days=1825,
            cert_type=CertType.INTERMEDIATE,
        )
        inter_cert = certificate_service.create_signed_cert(
            db, user1.id, inter_cert_data, issuer_cert=root_cert
        )
        db.add(
            CertificateChain(
                certificate_id=inter_cert.id,
                ca_certificate_data=inter_cert.certificate_data,
                level=1,
            )
        )
        db.commit()
        print("  -> Đã tạo Intermediate CA")

        # BƯỚC 4: TẠO END-USER CERT
        print("🔑 Tạo End-user Cert...")
        user_key = key_service.create_key(
            db, user1.id, KeyCreate(key_name="User Key", key_size=2048)
        )
        user_cert_data = CertificateCreate(
            cert_name="Chứng chỉ Giám Đốc",
            key_id=user_key.id,
            issuer="SecureSign Intermediate CA",
            subject="Giám Đốc Admin",
            valid_days=365,
            cert_type=CertType.END_USER,
        )
        user_cert = certificate_service.create_signed_cert(
            db, user1.id, user_cert_data, issuer_cert=inter_cert
        )
        db.add(
            CertificateChain(
                certificate_id=user_cert.id,
                ca_certificate_data=user_cert.certificate_data,
                level=2,
            )
        )
        db.commit()
        print("  -> Đã tạo End-user Cert")

        # ==========================================
        # BƯỚC 3: TẠO VĂN BẢN MẪU
        # ==========================================
        print("📄 Đang tạo dữ liệu Văn bản mẫu...")

        minimal_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n188\n%%EOF"

        file_hash = hashlib.sha256(minimal_pdf).hexdigest()
        upload_dir = "storage/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, "hop_dong_demo_2026.pdf")

        with open(file_path, "wb") as f:
            f.write(minimal_pdf)

        doc1 = Document(
            user_id=user1.id,
            file_name="hop_dong_demo_2026.pdf",
            original_file_path=file_path,
            file_size=len(minimal_pdf),
            mime_type="application/pdf",
            file_hash=file_hash,
        )
        db.add(doc1)
        db.commit()
        db.refresh(doc1)
        print(f"  -> Đã tạo tài liệu: {doc1.file_name}")

        print("\n✅ Hoàn thành Seed Data! Hệ thống đã sẵn sàng.")
        print("-" * 50)
        print("🚀 THÔNG TIN ĐĂNG NHẬP DEMO:")
        print("  - Tài khoản : admin")
        print("  - Mật khẩu  : 123456")
        print("-" * 50)

    except Exception as e:
        print(f"❌ Lỗi trong quá trình tạo dữ liệu mẫu: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force", action="store_true", help="Xoá dữ liệu cũ và seed lại"
    )
    args = parser.parse_args()

    seed_db(force=args.force)

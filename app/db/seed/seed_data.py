import sys
import os
import hashlib
import random
from datetime import datetime, timedelta, UTC

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base

# Import Models
from app.models.user import User
from app.models.document import Document
from app.models.certificate import Certificate, CertificateChain, CertType
from app.models.key import Key
from app.models.signature import Signature
from app.models.timestamp import Timestamp, Log, VerifyLog

# Import Services & Schemas
from app.core.security import get_password_hash
from app.schemas.key_schema import KeyCreate
from app.schemas.certificate_schema import CertificateCreate
from app.services.key_service import key_service
from app.services.certificate_service import certificate_service

# Cấu hình path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# ==========================================
# 1. SEED USERS
# ==========================================
def seed_users(db: Session):
    print("👤 Đang tạo Users...")
    users_data = [
        {"username": "admin", "pass": "123456"},
        {"username": "giamdoc_nguyen", "pass": "123456"},
        {"username": "nhanvien_tran", "pass": "123456"},
        {"username": "user1", "pass": "123456"},
        {"username": "user2", "pass": "123456"},
        {"username": "user3", "pass": "123456"},
        {"username": "user4", "pass": "123456"},
        {"username": "user5", "pass": "123456"},
        {"username": "user6", "pass": "123456"},
        {"username": "user7", "pass": "123456"},
        {"username": "user8", "pass": "123456"},
        {"username": "user9", "pass": "123456"},
        {"username": "user0", "pass": "123456"},
    ]

    created_users = {}
    for u in users_data:
        user = User(
            username=u["username"],
            password_hash=get_password_hash(u["pass"]),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        created_users[u["username"]] = user
        print(f"  -> Đã tạo user: {user.username}")

    return created_users


# ==========================================
# 2. SEED PKI (CA, TSA & User Certs)
# ==========================================
def seed_pki(db: Session, users: dict):
    print("🔑 Đang tạo Hệ thống Khóa & Chứng chỉ (PKI)...")
    admin = users["admin"]
    giamdoc = users["giamdoc_nguyen"]

    # 2.1. TẠO ROOT CA
    root_key = key_service.create_key(
        db, admin.id, KeyCreate(key_name="Root CA Key", key_size=2048)
    )
    root_cert_data = CertificateCreate(
        cert_name="SecureSign Root CA",
        key_id=root_key.id,
        issuer="SecureSign Root CA",
        subject="SecureSign Root CA",
        valid_days=3650,
        cert_type=CertType.ROOT,
    )
    root_cert = certificate_service.create_root_ca(db, admin.id, root_cert_data)
    db.add(
        CertificateChain(
            certificate_id=root_cert.id,
            ca_certificate_data=root_cert.certificate_data,
            level=0,
        )
    )
    print("  -> Đã tạo Root CA")

    # 2.2. TẠO INTERMEDIATE CA
    inter_key = key_service.create_key(
        db, admin.id, KeyCreate(key_name="Intermediate CA Key", key_size=2048)
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
        db, admin.id, inter_cert_data, issuer_cert=root_cert
    )
    db.add(
        CertificateChain(
            certificate_id=inter_cert.id,
            ca_certificate_data=inter_cert.certificate_data,
            level=1,
        )
    )
    print("  -> Đã tạo Intermediate CA")

    # 2.3. TẠO INTERNAL TSA CERTIFICATE
    tsa_key = key_service.create_key(
        db, admin.id, KeyCreate(key_name="Internal TSA Key", key_size=2048)
    )
    tsa_cert_data = CertificateCreate(
        cert_name="SecureSign Internal TSA",
        key_id=tsa_key.id,
        issuer="SecureSign Intermediate CA",
        subject="SecureSign TimeStamping Authority",
        valid_days=1825,
        cert_type=CertType.END_ENTITY,
    )
    tsa_cert = certificate_service.create_signed_cert(
        db, admin.id, tsa_cert_data, issuer_cert=inter_cert
    )
    tsa_cert.purpose = "timestamping"
    db.add(
        CertificateChain(
            certificate_id=tsa_cert.id,
            ca_certificate_data=tsa_cert.certificate_data,
            level=2,
        )
    )
    db.commit()
    print("  -> Đã tạo Internal TSA Certificate")

    # 2.4. TẠO CHỨNG CHỈ CHO GIÁM ĐỐC
    user_key = key_service.create_key(
        db, giamdoc.id, KeyCreate(key_name="Khóa Ký Hợp Đồng", key_size=2048)
    )
    user_cert_data = CertificateCreate(
        cert_name="Chứng chỉ Giám Đốc Nguyễn",
        key_id=user_key.id,
        issuer="SecureSign Intermediate CA",
        subject="Giám Đốc Nguyễn Văn A",
        valid_days=365,
        cert_type=CertType.END_ENTITY,
    )
    user_cert = certificate_service.create_signed_cert(
        db, giamdoc.id, user_cert_data, issuer_cert=inter_cert
    )
    user_cert.purpose = "document_signing"
    db.add(
        CertificateChain(
            certificate_id=user_cert.id,
            ca_certificate_data=user_cert.certificate_data,
            level=2,
        )
    )
    db.commit()
    print("  -> Đã tạo Chứng chỉ người dùng (Giám đốc)")

    return {"user_key": user_key, "user_cert": user_cert}


# ==========================================
# 3. SEED DOCUMENTS
# ==========================================
def seed_documents(db: Session, users: dict):
    print("📄 Đang tạo dữ liệu Văn bản mẫu...")
    upload_dir = "storage/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    giamdoc = users["giamdoc_nguyen"]
    nhanvien = users["nhanvien_tran"]

    minimal_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n188\n%%EOF"

    docs_info = [
        {
            "name": "hop_dong_thue_nha_2026.pdf",
            "user_id": giamdoc.id,
            "status": "SIGNED",
        },
        {
            "name": "don_xin_nghi_phep_T4.pdf",
            "user_id": nhanvien.id,
            "status": "UPLOADED",
        },
        {
            "name": "bao_cao_tai_chinh_Q1.pdf",
            "user_id": giamdoc.id,
            "status": "VERIFIED",
        },
    ]

    created_docs = []
    for doc in docs_info:
        file_hash = hashlib.sha256(minimal_pdf + doc["name"].encode()).hexdigest()
        file_path = os.path.join(upload_dir, doc["name"])

        with open(file_path, "wb") as f:
            f.write(minimal_pdf)

        new_doc = Document(
            user_id=doc["user_id"],
            file_name=doc["name"],
            original_file_path=file_path,
            signed_file_path=file_path if doc["status"] != "UPLOADED" else None,
            file_size=len(minimal_pdf),
            mime_type="application/pdf",
            file_hash=file_hash,
            signed_file_hash=file_hash if doc["status"] != "UPLOADED" else None,
            status=doc["status"],
        )
        db.add(new_doc)
        created_docs.append(new_doc)

    db.commit()
    print(f"  -> Đã tạo {len(created_docs)} tài liệu.")
    return created_docs


# ==========================================
# 4. SEED SIGNATURES & TIMESTAMPS
# ==========================================
def seed_signatures(db: Session, docs: list, pki_data: dict, users: dict):
    print("✍️ Đang tạo dữ liệu Chữ ký & Timestamp...")
    giamdoc = users["giamdoc_nguyen"]

    # Chỉ lấy các doc đã ký hoặc verified
    signed_docs = [d for d in docs if d.status in ["SIGNED", "VERIFIED"]]

    for doc in signed_docs:
        sig = Signature(
            document_id=doc.id,
            key_id=pki_data["user_key"].id,
            certificate_id=pki_data["user_cert"].id,
            user_id=giamdoc.id,
            signature_value=b"fake_signature_bytes_for_seed",
            hash_algorithm="SHA-256",
            signature_algorithm="RSA",
            visible_signature=True,
            signer_name="Nguyễn Văn A",
            signer_reason="Đã phê duyệt",
            signer_location="TP. Hồ Chí Minh",
        )
        db.add(sig)
        db.commit()
        db.refresh(sig)

        # Tạo giả lập Timestamp đi kèm chữ ký đó
        tsa = Timestamp(
            signature_id=sig.id,
            timestamp_token=b"fake_tsa_token_bytes",
            hashed_data="fake_hash_data",
            tsa_name="SecureSign Internal TSA",
        )
        db.add(tsa)

    db.commit()
    print("  -> Đã tạo dữ liệu Chữ ký và TSA thành công.")


# ==========================================
# 5. SEED LOGS & VERIFY LOGS
# ==========================================
def seed_logs(db: Session, docs: list, users: dict):
    print("📊 Đang tạo dữ liệu Logs & Audit...")

    # Lấy tất cả signature đã tạo
    signatures = db.query(Signature).all()

    if not signatures:
        print("⚠️ Không có signature nào để tạo verify log")
        return

    # 5.1 Verify Logs
    verified_docs = [d for d in docs if d.status == "VERIFIED"]

    for doc in verified_docs:
        sig = random.choice(signatures)  # 👉 chọn signature thật

        v_log = VerifyLog(
            document_id=doc.id,
            signature_id=sig.id,
            is_valid=True,
            message="Chữ ký hợp lệ. Chứng chỉ toàn vẹn.",
            created_at=datetime.now(UTC) - timedelta(hours=random.randint(1, 48)),
        )
        db.add(v_log)

    db.commit()
    print("  -> Đã tạo Audit Logs và Verify Logs.")


# ==========================================
# MAIN EXECUTION
# ==========================================
def run_seed(force=False):
    print("🌱 BẮT ĐẦU QUÁ TRÌNH TẠO DỮ LIỆU MẪU (SEED DATA)...")
    db = SessionLocal()

    try:
        # 1. Khởi tạo Schema
        Base.metadata.create_all(bind=engine)

        # 2. Kiểm tra tồn tại
        admin = db.query(User).filter(User.username == "admin").first()
        if admin and not force:
            print("⚠️ Dữ liệu mẫu đã tồn tại. Dùng tham số --force để ghi đè.")
            return

        # 3. Clean DB nếu Force = True
        if force:
            print("♻️ Xóa dữ liệu cũ (Cascade)...")
            db.query(Log).delete()
            db.query(VerifyLog).delete()
            db.query(Timestamp).delete()
            db.query(Signature).delete()
            db.query(Document).delete()
            db.query(CertificateChain).delete()
            db.query(Certificate).delete()
            db.query(Key).delete()
            db.query(User).delete()
            db.commit()

        # 4. Thực thi từng Module
        created_users = seed_users(db)
        pki_data = seed_pki(db, created_users)
        created_docs = seed_documents(db, created_users)
        seed_signatures(db, created_docs, pki_data, created_users)
        seed_logs(db, created_docs, created_users)

        print("-" * 50)
        print("✅ HOÀN TẤT SEED DATA! HỆ THỐNG ĐÃ SẴN SÀNG.")
        print("🚀 THÔNG TIN ĐĂNG NHẬP DEMO:")
        print("  - Admin: admin / 123456")
        print("  - Giám Đốc: giamdoc_nguyen / 123456")
        print("  - Nhân Viên: nhanvien_tran / 123456")
        print("  - Khác: user0->9 / 123456")
        print("-" * 50)

    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng trong quá trình Seed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force", action="store_true", help="Xoá dữ liệu cũ và seed lại toàn bộ"
    )
    args = parser.parse_args()

    run_seed(force=args.force)

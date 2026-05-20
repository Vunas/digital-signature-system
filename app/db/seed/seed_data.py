import sys
import os
import hashlib
import random
import asyncio
from datetime import datetime, timedelta, UTC

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base

# Import Models
from app.models.user import User
from app.models.document import Document
from app.models.certificate import Certificate, CertificateChain, CertType
from app.models.key import Key
from app.models.signature import Signature
from app.models.timestamp import Timestamp
from app.models.audit_log import AuditLog
from app.models.verify_log import VerifyLog

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
async def seed_users(db: AsyncSession):
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

        await db.commit()
        await db.refresh(user)

        created_users[u["username"]] = user

        print(f"  -> Đã tạo user: {user.username}")

    return created_users


# ==========================================
# 2. SEED PKI
# ==========================================
async def seed_pki(db: AsyncSession, users: dict):
    print("🔑 Đang tạo Hệ thống PKI...")

    admin = users["admin"]
    giamdoc = users["giamdoc_nguyen"]

    # ROOT CA
    root_key = await key_service.create_key(
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

    root_cert = await certificate_service.create_root_ca(db, admin.id, root_cert_data)

    db.add(
        CertificateChain(
            certificate_id=root_cert.id,
            ca_certificate_data=root_cert.certificate_data,
            level=0,
        )
    )

    print("  -> Đã tạo Root CA")

    # INTERMEDIATE CA
    inter_key = await key_service.create_key(
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

    inter_cert = await certificate_service.create_signed_cert(
        db,
        admin.id,
        inter_cert_data,
        issuer_cert=root_cert,
    )

    db.add(
        CertificateChain(
            certificate_id=inter_cert.id,
            ca_certificate_data=inter_cert.certificate_data,
            level=1,
        )
    )

    print("  -> Đã tạo Intermediate CA")

    # TSA CERT
    tsa_key = await key_service.create_key(
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

    tsa_cert = await certificate_service.create_signed_cert(
        db,
        admin.id,
        tsa_cert_data,
        issuer_cert=inter_cert,
    )

    tsa_cert.purpose = "timestamping"

    db.add(
        CertificateChain(
            certificate_id=tsa_cert.id,
            ca_certificate_data=tsa_cert.certificate_data,
            level=2,
        )
    )

    await db.commit()

    print("  -> Đã tạo TSA Certificate")

    # USER CERT
    user_key = await key_service.create_key(
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

    user_cert = await certificate_service.create_signed_cert(
        db,
        giamdoc.id,
        user_cert_data,
        issuer_cert=inter_cert,
    )

    user_cert.purpose = "document_signing"

    db.add(
        CertificateChain(
            certificate_id=user_cert.id,
            ca_certificate_data=user_cert.certificate_data,
            level=2,
        )
    )

    await db.commit()

    print("  -> Đã tạo chứng chỉ người dùng")

    return {"user_key": user_key, "user_cert": user_cert}


# ==========================================
# 3. SEED DOCUMENTS
# ==========================================
async def seed_documents(db: AsyncSession, users: dict):
    print("📄 Đang tạo Documents...")

    upload_dir = "storage/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    giamdoc = users["giamdoc_nguyen"]
    nhanvien = users["nhanvien_tran"]

    minimal_pdf = b"%PDF-1.4 fake"

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

    await db.commit()

    for doc in created_docs:
        await db.refresh(doc)

    print(f"  -> Đã tạo {len(created_docs)} tài liệu")

    return created_docs


# ==========================================
# 4. SIGNATURES
# ==========================================
async def seed_signatures(
    db: AsyncSession,
    docs: list,
    pki_data: dict,
    users: dict,
):
    print("✍️ Đang tạo Signatures...")

    giamdoc = users["giamdoc_nguyen"]

    signed_docs = [d for d in docs if d.status in ["SIGNED", "VERIFIED"]]

    for doc in signed_docs:
        sig = Signature(
            document_id=doc.id,
            key_id=pki_data["user_key"].id,
            certificate_id=pki_data["user_cert"].id,
            user_id=giamdoc.id,
            signature_value=b"fake_signature",
            hash_algorithm="SHA-256",
            signature_algorithm="RSA",
            visible_signature=True,
            signer_name="Nguyễn Văn A",
            signer_reason="Đã phê duyệt",
            signer_location="TP. Hồ Chí Minh",
        )

        db.add(sig)

        await db.commit()
        await db.refresh(sig)

        tsa = Timestamp(
            signature_id=sig.id,
            timestamp_token=b"fake_tsa_token",
            hashed_data="fake_hash_data",
            tsa_name="SecureSign Internal TSA",
        )

        db.add(tsa)

    await db.commit()

    print("  -> Đã tạo Signatures & TSA")


# ==========================================
# 5. LOGS
# ==========================================
async def seed_logs(
    db: AsyncSession,
    docs: list,
    users: dict,
):
    print("📊 Đang tạo Logs...")

    result = await db.execute(select(Signature))
    signatures = result.scalars().all()

    if not signatures:
        print("⚠️ Không có signature nào")
        return

    verified_docs = [d for d in docs if d.status == "VERIFIED"]

    for doc in verified_docs:
        sig = random.choice(signatures)

        v_log = VerifyLog(
            document_id=doc.id,
            signature_id=sig.id,
            is_valid=True,
            message="Chữ ký hợp lệ",
            created_at=datetime.now(UTC) - timedelta(hours=random.randint(1, 48)),
        )

        db.add(v_log)

    await db.commit()

    print("  -> Đã tạo Verify Logs")


# ==========================================
# MAIN
# ==========================================
async def run_seed(force=False):
    print("🌱 BẮT ĐẦU SEED DATA...")

    async with AsyncSessionLocal() as db:
        try:
            # CREATE TABLES
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # CHECK ADMIN
            result = await db.execute(select(User).where(User.username == "admin"))

            admin = result.scalar_one_or_none()

            if admin and not force:
                print("⚠️ Seed đã tồn tại. Dùng --force để ghi đè.")
                return

            # FORCE CLEAN
            if force:
                print("♻️ Xóa dữ liệu cũ...")

                await db.execute(delete(AuditLog))
                await db.execute(delete(VerifyLog))
                await db.execute(delete(Timestamp))
                await db.execute(delete(Signature))
                await db.execute(delete(Document))
                await db.execute(delete(CertificateChain))
                await db.execute(delete(Certificate))
                await db.execute(delete(Key))
                await db.execute(delete(User))

                await db.commit()

            # RUN SEED
            created_users = await seed_users(db)

            pki_data = await seed_pki(db, created_users)

            created_docs = await seed_documents(db, created_users)

            await seed_signatures(db, created_docs, pki_data, created_users)

            await seed_logs(db, created_docs, created_users)

            print("-" * 50)
            print("✅ HOÀN TẤT SEED DATA")
            print("🚀 Admin: admin / 123456")
            print("🚀 Giám đốc: giamdoc_nguyen / 123456")
            print("-" * 50)

        except Exception as e:
            await db.rollback()
            print(f"❌ Lỗi seed: {e}")

        finally:
            await db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--force", action="store_true", help="Xóa dữ liệu cũ và seed lại")

    args = parser.parse_args()

    asyncio.run(run_seed(force=args.force))

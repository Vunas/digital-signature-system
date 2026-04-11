from sqlalchemy.orm import Session
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
)
import datetime

from app.schemas.certificate_schema import CertificateCreate
from app.repositories.certificate_repo import certificate_repo
from app.repositories.key_repo import key_repo
from app.services.crypto.aes_service import aes_service
from app.models.certificate import Certificate  # Import thêm model Certificate


class CertificateService:
    def _get_private_key(self, key_record, passphrase: str = None, raw_key: str = None):
        """Hàm phụ trợ lấy Private Key từ DB/Raw"""
        if key_record.storage_type == "local" or (
            hasattr(key_record.storage_type, "value")
            and key_record.storage_type.value == "local"
        ):
            if not raw_key:
                raise ValueError(
                    "Bắt buộc phải có Private Key thô để ký chứng chỉ Local."
                )
            return load_pem_private_key(raw_key.encode("utf-8"), password=None)
        else:
            if passphrase:
                try:
                    return load_pem_private_key(
                        key_record.private_key_encrypted,
                        password=passphrase.encode("utf-8"),
                    )
                except Exception:
                    raise ValueError("Passphrase giải mã khóa không chính xác!")
            else:
                priv_key_bytes = aes_service.decrypt_key(
                    key_record.private_key_encrypted
                )
                return load_pem_private_key(priv_key_bytes, password=None)

    def create_root_ca(self, db: Session, user_id: int, cert_data: CertificateCreate):
        """Tạo Root CA (Self-signed với quyền hạn CA)"""
        key_record = key_repo.get_by_id(db, cert_data.key_id, user_id)
        private_key = self._get_private_key(key_record)
        public_key = load_pem_public_key(key_record.public_key)

        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, cert_data.subject),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, cert_data.issuer),
                x509.NameAttribute(NameOID.COUNTRY_NAME, "VN"),
            ]
        )

        cert_builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(
                datetime.datetime.utcnow()
                + datetime.timedelta(days=cert_data.valid_days)
            )
            # CẤU HÌNH QUAN TRỌNG NHẤT: Bật cờ CA = True để nó có quyền cấp chứng chỉ con
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=True,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
        )

        certificate = cert_builder.sign(private_key, hashes.SHA256())

        return certificate_repo.create(
            db=db,
            user_id=user_id,
            key_id=key_record.id,
            cert_name=cert_data.cert_name,
            certificate_data=certificate.public_bytes(Encoding.DER),
            certificate_pem=certificate.public_bytes(Encoding.PEM).decode(),
            issuer=cert_data.issuer,
            subject=cert_data.subject,
            cert_type=cert_data.cert_type,
            serial_number=str(certificate.serial_number),
            valid_from=certificate.not_valid_before_utc,
            valid_to=certificate.not_valid_after_utc,
        )

    def create_signed_cert(
        self, db: Session, user_id: int, cert_data: CertificateCreate, issuer_cert
    ):
        """Tạo chứng chỉ con (Intermediate CA hoặc End-User) được ký bởi CA cấp trên."""
        # Lấy khóa Public của User cần tạo chứng chỉ
        user_key_record = key_repo.get_by_id(db, cert_data.key_id, user_id)
        user_public_key = load_pem_public_key(user_key_record.public_key)

        # Lấy khóa Private của Thằng Cấp Trên (Issuer) để đóng mộc
        issuer_key_record = key_repo.get_by_id(
            db, issuer_cert.key_id, issuer_cert.user_id
        )
        issuer_private_key = self._get_private_key(issuer_key_record)

        # Trích xuất Subject của thằng cấp trên để làm Issuer cho thằng con
        issuer_x509 = x509.load_der_x509_certificate(issuer_cert.certificate_data)

        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, cert_data.subject),
                x509.NameAttribute(NameOID.COUNTRY_NAME, "VN"),
            ]
        )

        # Xác định xem thằng con này là CA (Intermediate) hay chỉ là User thường
        is_ca = True if cert_data.cert_type == "intermediate" else False

        cert_builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer_x509.subject)  # Kế thừa Issuer từ CA cấp trên
            .public_key(user_public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(
                datetime.datetime.utcnow()
                + datetime.timedelta(days=cert_data.valid_days)
            )
            .add_extension(
                x509.BasicConstraints(ca=is_ca, path_length=0 if is_ca else None),
                critical=True,
            )
        )

        # Nếu là User thì chỉ được dùng để ký số (Digital Signature), không được quyền cấp chứng chỉ con (key_cert_sign)
        if not is_ca:
            cert_builder = cert_builder.add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=True,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )

        # CA CẤP TRÊN DÙNG KHÓA PRIVATE CỦA NÓ ĐỂ KÝ CHO CHỨNG CHỈ NÀY
        certificate = cert_builder.sign(issuer_private_key, hashes.SHA256())

        return certificate_repo.create(
            db=db,
            user_id=user_id,
            key_id=user_key_record.id,
            cert_name=cert_data.cert_name,
            certificate_data=certificate.public_bytes(Encoding.DER),
            certificate_pem=certificate.public_bytes(Encoding.PEM).decode(),
            issuer=issuer_x509.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[
                0
            ].value,
            subject=cert_data.subject,
            cert_type=cert_data.cert_type,
            serial_number=str(certificate.serial_number),
            valid_from=certificate.not_valid_before_utc,
            valid_to=certificate.not_valid_after_utc,
        )

    def get_root_ca(self, db: Session):
        """Lấy Root CA hiện tại của hệ thống"""
        return db.query(Certificate).filter(Certificate.cert_type == "root").first()

    def get_intermediate_ca(self, db: Session):
        """Lấy Intermediate CA hiện tại của hệ thống"""
        return (
            db.query(Certificate)
            .filter(Certificate.cert_type == "intermediate")
            .first()
        )


certificate_service = CertificateService()

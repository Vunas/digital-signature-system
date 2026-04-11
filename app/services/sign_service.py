from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives import serialization
from asn1crypto import pem, x509, keys
import os

# Import pyHanko để xử lý PDF và Timestamp
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.fields import SigSeedSubFilter
from pyhanko.sign.timestamps import HTTPTimeStamper

# QUAN TRỌNG: Import thêm SimpleCertificateStore để xử lý chuỗi chứng chỉ (Chain)
from pyhanko_certvalidator.registry import SimpleCertificateStore

from app.schemas.signature_schema import SignatureCreate
from app.repositories.document_repo import document_repo
from app.repositories.key_repo import key_repo
from app.repositories.certificate_repo import certificate_repo
from app.repositories.signature_repo import signature_repo
from app.services.crypto.aes_service import aes_service
from app.utils.file_utils import get_signed_file_path


class SignService:
    def sign_pdf(self, db: Session, user_id: int, sign_data: SignatureCreate):
        """Thực hiện nhúng chữ ký số chuẩn PAdES vào tệp PDF."""

        # 1. Lấy thông tin Document, Key, Certificate từ DB
        doc = document_repo.get_by_id(db, sign_data.document_id, user_id)
        key_record = key_repo.get_by_id(db, sign_data.key_id, user_id)
        cert_record = certificate_repo.get_by_key_id(db, key_record.id)

        if not doc or not key_record or not cert_record:
            raise ValueError("Dữ liệu không hợp lệ hoặc thiếu chứng chỉ.")

        input_pdf_path = doc.original_file_path
        output_pdf_path = get_signed_file_path(doc.file_name)

        # 2. Chuẩn bị Cryptography Objects từ DB (Xử lý giải mã tùy loại lưu trữ)
        private_key = None

        # Nếu là khóa Local, User bắt buộc phải gửi Raw Key lên
        if key_record.storage_type == "local" or (
            hasattr(key_record.storage_type, "value")
            and key_record.storage_type.value == "local"
        ):
            if not getattr(sign_data, "raw_private_key", None):
                raise ValueError(
                    "Vui lòng đính kèm file Private Key (.pem) từ máy của bạn để ký."
                )
            priv_key_bytes = sign_data.raw_private_key.encode("utf-8")
        else:
            # Nếu là khóa Server, giải mã bằng AES hoặc Passphrase
            if getattr(sign_data, "passphrase", None):
                # Mã hóa Zero-Knowledge
                priv_key_bytes = key_record.private_key_encrypted
            else:
                # Mã hóa Auto Master Key
                priv_key_bytes = aes_service.decrypt_key(
                    key_record.private_key_encrypted
                )

        # Load cryptography key (Có tính tới Passphrase)
        try:
            crypto_priv_key = load_pem_private_key(
                priv_key_bytes,
                password=(
                    sign_data.passphrase.encode("utf-8")
                    if getattr(sign_data, "passphrase", None)
                    else None
                ),
            )
        except Exception:
            raise ValueError(
                "Mật khẩu giải mã khóa không hợp lệ hoặc sai định dạng khóa."
            )

        # Chuyển đổi sang asn1crypto
        der_key_bytes = crypto_priv_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        private_key = keys.PrivateKeyInfo.load(der_key_bytes)

        # Load Certificate Người dùng (asn1crypto)
        cert_bytes = getattr(cert_record, "certificate_data", None)
        if not cert_bytes:
            cert_bytes = getattr(cert_record, "certificate_pem", None)

        if not cert_bytes:
            raise ValueError(
                "Không tìm thấy dữ liệu chứng chỉ (certificate_data) trong Database."
            )

        if isinstance(cert_bytes, str):
            cert_bytes = cert_bytes.encode("utf-8")

        if pem.detect(cert_bytes):
            _, _, der_cert_bytes = pem.unarmor(cert_bytes)
            end_user_cert = x509.Certificate.load(der_cert_bytes)
        else:
            end_user_cert = x509.Certificate.load(cert_bytes)

        # ==========================================
        # 2.5. XÂY DỰNG CHUỖI CHỨNG CHỈ (CERTIFICATE CHAIN)
        # ==========================================
        cert_registry = SimpleCertificateStore()

        # Lấy chứng chỉ Intermediate từ Database
        inter_cert_record = certificate_repo.get_by_name(
            db, "SecureSign Intermediate CA"
        )

        if inter_cert_record:
            inter_cert_bytes = getattr(inter_cert_record, "certificate_data", None)
            if not inter_cert_bytes:
                inter_cert_bytes = getattr(inter_cert_record, "certificate_pem", None)

            if inter_cert_bytes:
                if isinstance(inter_cert_bytes, str):
                    inter_cert_bytes = inter_cert_bytes.encode("utf-8")

                # Parse Intermediate cert tương tự end-user cert
                if pem.detect(inter_cert_bytes):
                    _, _, der_inter_bytes = pem.unarmor(inter_cert_bytes)
                    inter_cert = x509.Certificate.load(der_inter_bytes)
                else:
                    inter_cert = x509.Certificate.load(inter_cert_bytes)

                # Đăng ký chứng chỉ trung gian vào registry
                cert_registry.register(inter_cert)

        # Ghi chú: Thông thường CHỈ CẦN nhúng Intermediate CA vào PDF.
        # Root CA không cần nhúng (hoặc nhúng cũng không sao), vì tính hợp lệ của chữ ký
        # phụ thuộc vào việc Root CA đó đã được Trust (tin cậy) sẵn trong kho hệ thống
        # hoặc Adobe Approved Trust List (AATL) của người mở file chưa.

        # ==========================================
        # 3. CẤU HÌNH TIMESTAMPER (TSA)
        # ==========================================
        tsa_url = os.getenv("TSA_URL")
        timestamper = None
        if tsa_url:
            try:
                timestamper = HTTPTimeStamper(tsa_url)
            except Exception:
                timestamper = None

        # ==========================================
        # 4. KHỞI TẠO SIGNER CỦA PYHANKO KÈM CHAIN
        # ==========================================
        signer = signers.SimpleSigner(
            signing_cert=end_user_cert,
            signing_key=private_key,
            cert_registry=cert_registry,
        )

        # Thực hiện mở PDF và nhúng chữ ký
        with open(input_pdf_path, "rb") as input_file:
            pdf_writer = IncrementalPdfFileWriter(input_file, strict=False)

            # ==========================================
            # 5. CẤU HÌNH VISIBLE SIGNATURE (CON DẤU TRỰC QUAN)
            # ==========================================
            meta = signers.PdfSignatureMetadata(
                field_name="Signature1",
                location=sign_data.signer_location,
                reason=sign_data.signer_reason,
                name=sign_data.signer_name,
                subfilter=SigSeedSubFilter.ADOBE_PKCS7_DETACHED,
                validation_context=None,
                embed_validation_info=True if timestamper else False,
            )

            # Ghi file PDF đã ký ra disk
            with open(output_pdf_path, "wb") as output_file:
                try:
                    signers.sign_pdf(
                        pdf_writer,
                        meta,
                        signer=signer,
                        timestamper=timestamper,
                        existing_fields_only=False,
                        in_place=False,
                        output=output_file,
                    )
                except Exception as e:
                    # FALLBACK: Nếu lỗi TSA
                    if "timestamp" in str(e).lower() and timestamper:
                        input_file.seek(0)
                        pdf_writer = IncrementalPdfFileWriter(input_file, strict=False)
                        signers.sign_pdf(
                            pdf_writer,
                            meta,
                            signer=signer,
                            timestamper=None,
                            existing_fields_only=False,
                            output=output_file,
                        )
                    else:
                        raise e

        # 6. Lưu thông tin chữ ký vào Database
        signature_record = signature_repo.create(
            db=db,
            document_id=doc.id,
            key_id=key_record.id,
            certificate_id=cert_record.id,
            user_id=user_id,
            signer_name=sign_data.signer_name,
            signer_reason=sign_data.signer_reason,
            signer_location=sign_data.signer_location,
            visible_signature=True,
        )

        # Cập nhật trạng thái Document
        from app.models.document import DocumentStatus

        document_repo.update_status(
            db=db, db_obj=doc, status=DocumentStatus.SIGNED, signed_path=output_pdf_path
        )

        return signature_record


sign_service = SignService()

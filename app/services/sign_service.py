import os
import tempfile  # Thêm thư viện này
import requests
import logging

from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives import serialization
from asn1crypto import pem, x509, keys

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.fields import SigSeedSubFilter
from pyhanko.sign.timestamps import HTTPTimeStamper
from pyhanko_certvalidator.registry import SimpleCertificateStore

from app.schemas.signature_schema import SignatureCreate
from app.repositories.document_repo import document_repo
from app.repositories.key_repo import key_repo
from app.repositories.certificate_repo import certificate_repo
from app.repositories.signature_repo import signature_repo
from app.services.crypto.aes_service import aes_service

from app.utils.file_utils import (
    get_signed_file_path,
    get_file_content,
    save_signed_file_content,
)


class SignService:
    def sign_pdf(self, db: Session, user_id: int, sign_data: SignatureCreate):
        """Thực hiện nhúng chữ ký số chuẩn PAdES vào tệp PDF trên Cloud."""

        # 1. Lấy thông tin Document, Key, Certificate từ DB
        doc = document_repo.get_by_id(db, sign_data.document_id, user_id)
        key_record = key_repo.get_by_id(db, sign_data.key_id, user_id)
        cert_record = certificate_repo.get_by_key_id(db, key_record.id)

        if not doc or not key_record or not cert_record:
            raise ValueError("Dữ liệu không hợp lệ hoặc thiếu chứng chỉ.")

        # Đường dẫn trên Cloud Supabase
        input_db_path = doc.original_file_path
        output_db_path = get_signed_file_path(doc.file_name, input_db_path)

        # 2. Chuẩn bị Cryptography Objects từ DB
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
            if getattr(sign_data, "passphrase", None):
                priv_key_bytes = key_record.private_key_encrypted
            else:
                priv_key_bytes = aes_service.decrypt_key(
                    key_record.private_key_encrypted
                )

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

        # Load Certificate Người dùng
        cert_bytes = getattr(cert_record, "certificate_data", None) or getattr(
            cert_record, "certificate_pem", None
        )
        if not cert_bytes:
            raise ValueError("Không tìm thấy dữ liệu chứng chỉ trong Database.")
        if isinstance(cert_bytes, str):
            cert_bytes = cert_bytes.encode("utf-8")

        if pem.detect(cert_bytes):
            _, _, der_cert_bytes = pem.unarmor(cert_bytes)
            end_entity_cert = x509.Certificate.load(der_cert_bytes)
        else:
            end_entity_cert = x509.Certificate.load(cert_bytes)

        # 3. XÂY DỰNG CHUỖI CHỨNG CHỈ
        cert_registry = SimpleCertificateStore()
        inter_cert_record = certificate_repo.get_by_name(
            db, "SecureSign Intermediate CA"
        )
        if inter_cert_record:
            inter_cert_bytes = getattr(
                inter_cert_record, "certificate_data", None
            ) or getattr(inter_cert_record, "certificate_pem", None)
            if inter_cert_bytes:
                if isinstance(inter_cert_bytes, str):
                    inter_cert_bytes = inter_cert_bytes.encode("utf-8")
                if pem.detect(inter_cert_bytes):
                    _, _, der_inter_bytes = pem.unarmor(inter_cert_bytes)
                    inter_cert = x509.Certificate.load(der_inter_bytes)
                else:
                    inter_cert = x509.Certificate.load(inter_cert_bytes)
                cert_registry.register(inter_cert)

        # 4. CẤU HÌNH TIMESTAMPER
        tsa_url = os.getenv("TSA_URL")
        timestamper = None
        if tsa_url:
            try:
                requests.get(tsa_url, timeout=2)
                timestamper = HTTPTimeStamper(tsa_url)
            except Exception as e:
                logging.warning(f"External TSA không phản hồi: {e}")
                timestamper = None

        # 5. DOWNLOAD - KÝ - UPLOAD DÙNG TEMP FILE
        # Tạo 2 file tạm trên server để pyHanko có thể thao tác vật lý
        tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        try:
            # 5.1 Tải file từ Supabase xuống file tạm
            file_bytes = get_file_content(input_db_path)
            tmp_in.write(file_bytes)
            tmp_in.flush()

            signer = signers.SimpleSigner(
                signing_cert=end_entity_cert,
                signing_key=private_key,
                cert_registry=cert_registry,
            )

            # 5.2 Cho pyHanko đọc và ký trên file tạm
            with open(tmp_in.name, "rb") as input_file:
                pdf_writer = IncrementalPdfFileWriter(input_file, strict=False)
                meta = signers.PdfSignatureMetadata(
                    field_name="Signature1",
                    location=sign_data.signer_location,
                    reason=sign_data.signer_reason,
                    name=sign_data.signer_name,
                    subfilter=SigSeedSubFilter.PADES,
                    embed_validation_info=False,
                )

                with open(tmp_out.name, "wb") as output_file:
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
                        if timestamper:
                            input_file.seek(0)
                            pdf_writer = IncrementalPdfFileWriter(
                                input_file, strict=False
                            )
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

            # 5.3 Đẩy file đã ký ngược lên Supabase
            with open(tmp_out.name, "rb") as f:
                signed_bytes = f.read()
                save_signed_file_content(output_db_path, signed_bytes)

            # 6. Lưu thông tin vào Database
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

            from app.models.document import DocumentStatus

            document_repo.update_status(
                db=db,
                db_obj=doc,
                status=DocumentStatus.SIGNED,
                signed_path=output_db_path,
            )

            return signature_record

        finally:
            # Luôn dọn dẹp file tạm dù thành công hay có lỗi để chống tràn ổ cứng máy chủ
            tmp_in.close()
            tmp_out.close()
            if os.path.exists(tmp_in.name):
                os.remove(tmp_in.name)
            if os.path.exists(tmp_out.name):
                os.remove(tmp_out.name)


sign_service = SignService()

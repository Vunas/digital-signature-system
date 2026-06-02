import os
import asyncio
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import validation
from pyhanko_certvalidator import ValidationContext
from pyhanko_certvalidator.errors import PathBuildingError
from asn1crypto import x509
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.certificate import Certificate
from app.models.enums import CertType, TargetResourceType, ActionStatus
from app.services.log_service import log_service
from app.services.verify_log_service import verify_log_service


class VerifyService:
    async def verify_pdf_signature(self, db: AsyncSession, file_path: str, user_id: int = None):
        """
        Đọc tệp PDF và xác thực chữ ký nhúng bên trong (Bất đồng bộ).
        Ghi log vào cả AuditLog và VerifyLog.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError("Không tìm thấy file PDF để xác thực.")

        if os.path.getsize(file_path) == 0:
            msg = (
                "File PDF tải lên bị rỗng (0 bytes). Quá trình truyền file có thể đã bị gián đoạn."
            )
            await log_service.log_action(
                db=db,
                user_id=user_id,
                action="VERIFY_DOCUMENT",
                target_type=TargetResourceType.DOCUMENT,
                target_id=os.path.basename(file_path),
                status=ActionStatus.FAILED,
                payload={"reason": "File rỗng"},
            )
            await verify_log_service.create_verify_log(
                db=db,
                document_id=None,
                signature_id=None,
                verified_by_user_id=user_id,
                is_valid=False,
                message=msg,
            )

            return {
                "is_valid": False,
                "is_integrity_valid": False,
                "is_cert_valid": False,
                "message": msg,
                "signer_info": None,
            }

        try:
            # Lấy chuỗi niềm tin (Trust Chain) từ DB
            root_result = await db.execute(
                select(Certificate).filter(Certificate.cert_type == CertType.ROOT)
            )
            root_records = root_result.scalars().all()

            inter_result = await db.execute(
                select(Certificate).filter(Certificate.cert_type == CertType.INTERMEDIATE)
            )
            inter_records = inter_result.scalars().all()

            trust_roots = [
                x509.Certificate.load(r.certificate_data)
                for r in root_records
                if r.certificate_data
            ]
            other_certs = [
                x509.Certificate.load(i.certificate_data)
                for i in inter_records
                if i.certificate_data
            ]

            if not trust_roots:
                msg = "Hệ thống chưa có Root CA để đối chiếu. Vui lòng chạy Seed Data."
                await verify_log_service.create_verify_log(
                    db=db,
                    document_id=None,
                    signature_id=None,
                    verified_by_user_id=user_id,
                    is_valid=False,
                    message=msg,
                )
                return {
                    "is_valid": False,
                    "is_integrity_valid": False,
                    "is_cert_valid": False,
                    "message": msg,
                    "signer_info": None,
                }

            vc = ValidationContext(trust_roots=trust_roots, other_certs=other_certs)

            # Phân tích file (I/O) chạy ngầm trong Thread
            result = await asyncio.to_thread(self._sync_verify_pdf, file_path, vc)

            # Ghi log Audit chống chối bỏ
            await log_service.log_action(
                db=db,
                user_id=user_id,
                action="VERIFY_DOCUMENT",
                target_type=TargetResourceType.DOCUMENT,
                target_id=os.path.basename(file_path),
                status=ActionStatus.SUCCESS if result.get("is_valid") else ActionStatus.FAILED,
                payload={"message": result.get("message")},
            )

            # Ghi log Verify chi tiết về trạng thái chữ ký (lưu cục JSON sạch)
            await verify_log_service.create_verify_log(
                db=db,
                document_id=None,
                signature_id=None,
                verified_by_user_id=user_id,
                is_valid=result.get("is_valid", False),
                is_integrity_valid=result.get("is_integrity_valid"),
                is_cert_valid=result.get("is_cert_valid"),
                message=result.get("message"),
                signer_snapshot=result.get("signer_info"),
            )

            return result

        except PathBuildingError:
            msg = "Chữ ký KHÔNG HỢP LỆ. Không thể xác minh nguồn gốc chứng chỉ (Chứng chỉ giả mạo hoặc cấp bởi bên thứ 3)."
            await log_service.log_action(
                db=db,
                user_id=user_id,
                action="VERIFY_DOCUMENT",
                target_type=TargetResourceType.DOCUMENT,
                target_id=os.path.basename(file_path),
                status=ActionStatus.FAILED,
                payload={"reason": "PathBuildingError"},
            )
            await verify_log_service.create_verify_log(
                db=db,
                document_id=None,
                signature_id=None,
                verified_by_user_id=user_id,
                is_valid=False,
                message=msg,
            )

            return {
                "is_valid": False,
                "is_integrity_valid": False,
                "is_cert_valid": False,
                "message": msg,
                "signer_info": None,
            }

        except Exception as e:
            msg = f"Lỗi hệ thống khi phân tích mã PDF: {str(e)}"
            await log_service.log_action(
                db=db,
                user_id=user_id,
                action="VERIFY_DOCUMENT",
                target_type=TargetResourceType.DOCUMENT,
                target_id=os.path.basename(file_path),
                status=ActionStatus.FAILED,
                payload={"reason": str(e)},
            )
            await verify_log_service.create_verify_log(
                db=db,
                document_id=None,
                signature_id=None,
                verified_by_user_id=user_id,
                is_valid=False,
                message=msg,
            )

            return {
                "is_valid": False,
                "is_integrity_valid": False,
                "is_cert_valid": False,
                "message": msg,
                "signer_info": None,
            }

    def _sync_verify_pdf(self, file_path: str, vc: ValidationContext):
        with open(file_path, "rb") as doc_file:
            reader = PdfFileReader(doc_file, strict=False)

            embedded_signatures = reader.embedded_signatures
            if not embedded_signatures:
                return {
                    "is_valid": False,
                    "is_integrity_valid": False,
                    "is_cert_valid": False,
                    "message": "Văn bản chưa được ký điện tử (Không tìm thấy trường chữ ký).",
                    "signer_info": None,
                }

            sig_field = embedded_signatures[-1]
            signer_cert = getattr(sig_field, "signer_cert", None)

            status = validation.validate_pdf_signature(sig_field, signer_validation_context=vc)

            subject_info = (
                signer_cert.subject.human_friendly
                if signer_cert and hasattr(signer_cert.subject, "human_friendly")
                else "Không xác định"
            )
            issuer_info = (
                signer_cert.issuer.human_friendly
                if signer_cert and hasattr(signer_cert.issuer, "human_friendly")
                else "Không xác định"
            )

            sig_dict = sig_field.sig_object
            reason = sig_dict.get("/Reason", "")
            reason_str = reason.decode("utf-8") if hasattr(reason, "decode") else str(reason)

            # Xác định mức độ toàn vẹn của file (có bị chèn thêm nội dung sau khi ký hay không)
            is_entire_file = status.coverage.name == "ENTIRE_FILE"

            # Tạo dictionary dữ liệu thuần túy (Không dính HTML)
            signer_info_dict = {
                "subject": subject_info,
                "issuer": issuer_info,
                "reason": reason_str or "Không xác định",
                "has_tsa": bool(status.timestamp_validity),
                "is_entire_file": is_entire_file,
                "coverage_name": status.coverage.name,
            }

            if status.valid and status.intact:
                return {
                    "is_valid": True,
                    "is_integrity_valid": True,
                    "is_cert_valid": True,
                    "message": "Kiểm tra chữ ký thành công.",
                    "signer_info": signer_info_dict,
                }
            else:
                return {
                    "is_valid": False,
                    "is_integrity_valid": status.intact,
                    "is_cert_valid": status.valid,
                    "message": "Chữ ký KHÔNG HỢP LỆ. Văn bản đã bị phá vỡ cấu trúc gốc hoặc chứng chỉ bị thu hồi/giả mạo.",
                    "signer_info": signer_info_dict,
                }


verify_service = VerifyService()

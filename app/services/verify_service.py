import os
import asyncio
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import validation
from pyhanko_certvalidator import ValidationContext
from pyhanko_certvalidator.errors import PathBuildingError
from asn1crypto import x509
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.certificate import Certificate

# Centralized Enums (Fixed Imports)
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

            # Ghi log Verify chi tiết về trạng thái chữ ký
            await verify_log_service.create_verify_log(
                db=db,
                document_id=None,  # Nếu truyền từ router xuống có thể gắn document_id vào
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

            if status.coverage.name == "ENTIRE_FILE":
                coverage_str = "<span class='text-emerald-600 font-bold'><i class='fa-solid fa-check-circle mr-1'></i> Toàn vẹn 100% (Không có sửa đổi nào sau khi ký)</span>"
                main_message = "Chữ ký HỢP LỆ. Dữ liệu nguyên vẹn tuyệt đối và chứng chỉ hoàn toàn KHỚP với Root CA của hệ thống."
            else:
                coverage_str = "<span class='text-amber-600 font-bold'><i class='fa-solid fa-triangle-exclamation mr-1'></i> Có nội dung mới (Highlight, Comment...) chèn thêm sau khi ký</span>"
                main_message = "Chữ ký HỢP LỆ trên dữ liệu gốc. <br><span class='text-amber-600 mt-2 block'>⚠️ TUY NHIÊN: Phát hiện tài liệu đã bị sửa đổi/chèn thêm sau thời điểm ký!</span>"

            tsa_str = (
                "<span class='text-emerald-600 font-bold'><i class='fa-solid fa-clock mr-1'></i> Có (Timestamp Authority)</span>"
                if status.timestamp_validity
                else "<span class='text-gray-500 font-bold'><i class='fa-solid fa-desktop mr-1'></i> Không (Thời gian từ máy tính)</span>"
            )

            full_signer_html = (
                f"<ul class='space-y-3 mt-4 text-left bg-white p-4 rounded-lg border border-gray-100 shadow-sm'>"
                f"<li class='pb-2 border-b border-gray-50'><b class='text-gray-500 block mb-1 text-[10px] uppercase tracking-wider'>Người ký (Subject)</b> <span class='text-indigo-700 font-bold text-sm'>{subject_info}</span></li>"
                f"<li class='pb-2 border-b border-gray-50'><b class='text-gray-500 block mb-1 text-[10px] uppercase tracking-wider'>Đơn vị cấp (Issuer)</b> <span class='text-gray-800 text-sm'>{issuer_info}</span></li>"
                f"<li class='pb-2 border-b border-gray-50'><b class='text-gray-500 block mb-1 text-[10px] uppercase tracking-wider'>Lý do ký (Reason)</b> <span class='text-gray-800 text-sm'>{reason_str or 'Không xác định'}</span></li>"
                f"<li class='pb-2 border-b border-gray-50 flex justify-between items-center'><b class='text-gray-500 text-[10px] uppercase tracking-wider'>Nguồn thời gian</b> <span class='text-sm'>{tsa_str}</span></li>"
                f"<li class='pt-1 bg-amber-50 -mx-4 -mb-4 p-4 rounded-b-lg border-t border-amber-100'><b class='text-gray-600 block mb-1 text-[10px] uppercase tracking-wider'>Tình trạng tài liệu</b> <span class='text-sm block'>{coverage_str}</span></li>"
                f"</ul>"
            )

            if status.valid and status.intact:
                return {
                    "is_valid": True,
                    "is_integrity_valid": True,
                    "is_cert_valid": True,
                    "message": main_message,
                    "signer_info": {"subject": full_signer_html, "coverage": status.coverage.name},
                }
            else:
                return {
                    "is_valid": False,
                    "is_integrity_valid": status.intact,
                    "is_cert_valid": status.valid,
                    "message": "Chữ ký KHÔNG HỢP LỆ. Văn bản đã bị phá vỡ cấu trúc gốc hoặc chứng chỉ bị thu hồi/giả mạo.",
                    "signer_info": {"subject": full_signer_html},
                }


verify_service = VerifyService()

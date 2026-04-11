from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import validation
from pyhanko_certvalidator import ValidationContext
from pyhanko_certvalidator.errors import PathBuildingError
from asn1crypto import x509
from sqlalchemy.orm import Session
import os
import concurrent.futures

from app.models.certificate import Certificate


class VerifyService:
    def verify_pdf_signature(self, db: Session, file_path: str):
        """
        Đọc tệp PDF và xác thực chữ ký nhúng bên trong.
        Quét Root CA & Intermediate CA từ Database để xác thực chuỗi (Path Building).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError("Không tìm thấy file PDF để xác thực.")

        # Kiểm tra file rỗng
        if os.path.getsize(file_path) == 0:
            return {
                "is_valid": False,
                "message": "File PDF tải lên bị rỗng (0 bytes). Quá trình truyền file có thể đã bị gián đoạn.",
                "signer_info": None,
            }

        try:
            # ==========================================
            # 1. TRÍCH XUẤT ROOT CA VÀ INTERMEDIATE CA TỪ DB
            # ==========================================
            root_records = (
                db.query(Certificate).filter(Certificate.cert_type == "root").all()
            )
            inter_records = (
                db.query(Certificate)
                .filter(Certificate.cert_type == "intermediate")
                .all()
            )

            trust_roots = []
            for r in root_records:
                if r.certificate_data:
                    trust_roots.append(x509.Certificate.load(r.certificate_data))

            other_certs = []
            for i in inter_records:
                if i.certificate_data:
                    other_certs.append(x509.Certificate.load(i.certificate_data))

            if not trust_roots:
                return {
                    "is_valid": False,
                    "message": "Hệ thống chưa có Root CA để đối chiếu. Vui lòng chạy Seed Data.",
                    "signer_info": None,
                }

            # ==========================================
            # 2. KHỞI TẠO VALIDATION CONTEXT NGHIÊM NGẶT
            # ==========================================
            vc = ValidationContext(trust_roots=trust_roots, other_certs=other_certs)

            # ==========================================
            # 3. TIẾN HÀNH KIỂM TRA FILE PDF
            # ==========================================
            with open(file_path, "rb") as doc_file:
                reader = PdfFileReader(doc_file, strict=False)

                embedded_signatures = reader.embedded_signatures
                if not embedded_signatures:
                    return {
                        "is_valid": False,
                        "message": "Văn bản chưa được ký điện tử (Không tìm thấy trường chữ ký).",
                        "signer_info": None,
                    }

                # Lấy lớp chữ ký mới nhất
                sig_field = embedded_signatures[-1]
                signer_cert = getattr(sig_field, "signer_cert", None)

                # Chạy validate bằng Thread (tránh block event loop của FastAPI)
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        validation.validate_pdf_signature,
                        sig_field,
                        signer_validation_context=vc,
                    )
                    status = future.result()

                # Trích xuất thông tin
                subject_info = "Không xác định"
                issuer_info = "Không xác định"

                if signer_cert:
                    if hasattr(signer_cert.subject, "human_friendly"):
                        subject_info = signer_cert.subject.human_friendly
                    else:
                        subject_info = str(signer_cert.subject)

                    if hasattr(signer_cert.issuer, "human_friendly"):
                        issuer_info = signer_cert.issuer.human_friendly
                    else:
                        issuer_info = str(signer_cert.issuer)

                sig_dict = sig_field.sig_object
                reason = sig_dict.get("/Reason", "")

                reason_str = (
                    reason.decode("utf-8") if hasattr(reason, "decode") else str(reason)
                )

                # ==========================================
                # 4. CHUYÊN NGHIỆP HÓA CẢNH BÁO (GIỐNG ADOBE)
                # ==========================================
                coverage_name = status.coverage.name

                if coverage_name == "ENTIRE_FILE":
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

                # Đóng gói HTML thành bảng chuyên nghiệp
                full_signer_html = (
                    f"<ul class='space-y-3 mt-4 text-left bg-white p-4 rounded-lg border border-gray-100 shadow-sm'>"
                    f"<li class='pb-2 border-b border-gray-50'><b class='text-gray-500 block mb-1 text-[10px] uppercase tracking-wider'>Người ký (Subject)</b> <span class='text-indigo-700 font-bold text-sm'>{subject_info}</span></li>"
                    f"<li class='pb-2 border-b border-gray-50'><b class='text-gray-500 block mb-1 text-[10px] uppercase tracking-wider'>Đơn vị cấp (Issuer)</b> <span class='text-gray-800 text-sm'>{issuer_info}</span></li>"
                    f"<li class='pb-2 border-b border-gray-50'><b class='text-gray-500 block mb-1 text-[10px] uppercase tracking-wider'>Lý do ký (Reason)</b> <span class='text-gray-800 text-sm'>{reason_str or 'Không xác định'}</span></li>"
                    f"<li class='pb-2 border-b border-gray-50 flex justify-between items-center'><b class='text-gray-500 text-[10px] uppercase tracking-wider'>Nguồn thời gian</b> <span class='text-sm'>{tsa_str}</span></li>"
                    f"<li class='pt-1 bg-amber-50 -mx-4 -mb-4 p-4 rounded-b-lg border-t border-amber-100'><b class='text-gray-600 block mb-1 text-[10px] uppercase tracking-wider'>Tình trạng tài liệu</b> <span class='text-sm block'>{coverage_str}</span></li>"
                    f"</ul>"
                )

                # ==========================================
                # 5. KẾT LUẬN TRẢ VỀ FRONTEND
                # ==========================================
                if status.valid and status.intact:
                    return {
                        "is_valid": True,
                        "message": main_message,
                        "signer_info": {
                            "subject": full_signer_html,
                            "coverage": status.coverage.name,
                        },
                    }
                else:
                    return {
                        "is_valid": False,
                        "message": "Chữ ký KHÔNG HỢP LỆ. Văn bản đã bị phá vỡ cấu trúc gốc hoặc chứng chỉ bị thu hồi/giả mạo.",
                        "signer_info": {"subject": full_signer_html},
                    }

        except PathBuildingError:
            # Bắt riêng lỗi "Không thể dò ra Root CA"
            return {
                "is_valid": False,
                "message": "Chữ ký KHÔNG HỢP LỆ. Không thể xác minh nguồn gốc chứng chỉ (Chứng chỉ giả mạo hoặc cấp bởi bên thứ 3).",
                "signer_info": None,
            }
        except Exception as e:
            return {
                "is_valid": False,
                "message": f"Lỗi hệ thống khi phân tích mã PDF: {str(e)}",
                "signer_info": None,
            }


verify_service = VerifyService()

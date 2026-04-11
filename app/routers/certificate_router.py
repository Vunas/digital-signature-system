from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.certificate_schema import CertificateCreate, CertificateResponse
from app.services.certificate_service import certificate_service

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.post("/", response_model=CertificateResponse)
def create_certificate(
    cert_data: CertificateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tạo một chứng chỉ End-User mới.
    Chứng chỉ này sẽ do Intermediate CA của hệ thống đứng ra cấp phát (Ký).
    """
    try:
        # Lấy Intermediate CA làm người cấp phát (Issuer)
        issuer_cert = certificate_service.get_intermediate_ca(db)
        if not issuer_cert:
            raise ValueError(
                "Hệ thống chưa thiết lập Intermediate CA. Vui lòng chạy Seed Data."
            )

        return certificate_service.create_signed_cert(
            db, current_user.id, cert_data, issuer_cert=issuer_cert
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/download-root-ca")
def download_root_ca(db: Session = Depends(get_db)):
    """
    Tải xuống Root CA (định dạng .cer)
    Người dùng chỉ cần cài file này 1 lần duy nhất vào Adobe Acrobat.
    """
    root_ca = certificate_service.get_root_ca(db)

    if not root_ca:
        raise HTTPException(
            status_code=404,
            detail="Chưa có Root CA trong hệ thống. Vui lòng chạy Seed Data trước.",
        )

    # Trả về file định dạng DER chuẩn, trình duyệt sẽ tự động tải file .cer về máy
    return Response(
        content=root_ca.certificate_data,
        media_type="application/x-x509-ca-cert",
        headers={
            "Content-Disposition": 'attachment; filename="SecureSign_Root_CA.cer"'
        },
    )

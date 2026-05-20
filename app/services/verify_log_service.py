from sqlalchemy.ext.asyncio import AsyncSession
from app.models.verify_log import VerifyLog


class VerifyLogService:
    async def create_verify_log(
        self,
        db: AsyncSession,
        document_id: int | None,
        signature_id: int | None,
        verified_by_user_id: int | None,
        is_valid: bool,
        is_integrity_valid: bool | None = None,
        is_cert_valid: bool | None = None,
        is_not_revoked: bool | None = None,
        message: str | None = None,
        signer_snapshot: dict | None = None,
    ) -> VerifyLog:

        verify_log = VerifyLog(
            document_id=document_id,
            signature_id=signature_id,
            verified_by_user_id=verified_by_user_id,
            is_valid=is_valid,
            is_integrity_valid=is_integrity_valid,
            is_cert_valid=is_cert_valid,
            is_not_revoked=is_not_revoked,
            message=message,
            signer_snapshot=signer_snapshot,
        )

        db.add(verify_log)
        await db.flush()

        return verify_log


verify_log_service = VerifyLogService()

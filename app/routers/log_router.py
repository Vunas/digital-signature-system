from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import desc
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.verify_log import VerifyLog
from app.schemas.log_schema import AuditLogResponse, VerifyLogResponse

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách Audit Logs (vết hệ thống)."""
    # Lọc log của chính user hiện tại để hiển thị (Admin có thể bỏ filter này)
    result = await db.execute(
        select(AuditLog)
        .filter(AuditLog.user_id == current_user.id)
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/verify", response_model=List[VerifyLogResponse])
async def get_verify_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy lịch sử xác thực văn bản của User hiện tại."""
    result = await db.execute(
        select(VerifyLog)
        .filter(VerifyLog.verified_by_user_id == current_user.id)
        .order_by(desc(VerifyLog.created_at))
        .limit(limit)
    )
    return result.scalars().all()

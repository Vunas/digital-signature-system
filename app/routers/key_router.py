from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.key_schema import KeyCreate, KeyResponse
from app.services.key_service import key_service
from app.repositories.key_repo import key_repo

router = APIRouter(prefix="/api/keys", tags=["Keys"])


@router.post("/", response_model=KeyResponse)
async def generate_new_key(
    key_data: KeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tạo một cặp khóa RSA mới và lưu trên Server."""
    try:
        new_key = await key_service.create_key(db, current_user.id, key_data)
        await db.commit()  # Chốt lưu db_key và log
        return new_key
    except Exception as e:
        await db.rollback()
        raise e


@router.get("/", response_model=List[KeyResponse])
async def get_my_keys(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Lấy danh sách các khóa của tôi."""
    return await key_repo.get_all_by_user(db, current_user.id)

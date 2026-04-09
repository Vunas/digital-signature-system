from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.key_schema import KeyCreate, KeyResponse
from app.services.key_service import create_user_keypair

router = APIRouter(prefix="/keys", tags=["Key Management"])


# Dummy class thay thế tạm cho get_current_user trong lúc review
class MockUser:
    id: int = 1


@router.post("/generate", response_model=KeyResponse)
def generate_key(
    key_in: KeyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(lambda: MockUser()),
):
    """
    Tạo cặp khóa công khai / bí mật mới cho user.
    """
    if key_in.storage_type not in ["server", "local"]:
        raise HTTPException(status_code=400, detail="Invalid storage type")

    new_key, raw_private = create_user_keypair(
        db=db,
        user_id=current_user.id,
        key_name=key_in.key_name,
        storage_type=key_in.storage_type,
        passphrase=key_in.passphrase,
        key_size=key_in.key_size,
    )

    # Chuyển đổi sang dict để thêm raw_private_key vào response
    response_data = KeyResponse.from_orm(new_key).dict()
    response_data["raw_private_key"] = raw_private

    return response_data


@router.get("/", response_model=list[KeyResponse])
def get_my_keys(
    db: Session = Depends(get_db), current_user=Depends(lambda: MockUser())
):
    from app.models.key import Key

    return db.query(Key).filter(Key.user_id == current_user.id).all()

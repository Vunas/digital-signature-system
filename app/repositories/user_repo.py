from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.core.security import get_password_hash


class UserRepository:
    def get_by_username(self, db: Session, username: str):
        return db.query(User).filter(User.username == username).first()

    def get_by_id(self, db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    def create(self, db: Session, obj_in: UserCreate):
        hashed_password = get_password_hash(obj_in.password)
        db_obj = User(username=obj_in.username, password_hash=hashed_password)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


user_repo = UserRepository()

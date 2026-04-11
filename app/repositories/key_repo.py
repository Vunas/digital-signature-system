from sqlalchemy.orm import Session
from app.models.key import Key


class KeyRepository:
    def get_by_id(self, db: Session, key_id: int, user_id: int):
        return db.query(Key).filter(Key.id == key_id, Key.user_id == user_id).first()

    def get_all_by_user(self, db: Session, user_id: int):
        return db.query(Key).filter(Key.user_id == user_id).all()

    def create(self, db: Session, **kwargs):
        db_obj = Key(**kwargs)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


key_repo = KeyRepository()

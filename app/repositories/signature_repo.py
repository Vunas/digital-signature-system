from sqlalchemy.orm import Session
from app.models.signature import Signature


class SignatureRepository:
    def get_by_document(self, db: Session, document_id: int):
        return db.query(Signature).filter(Signature.document_id == document_id).all()

    def create(self, db: Session, **kwargs):
        db_obj = Signature(**kwargs)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


signature_repo = SignatureRepository()

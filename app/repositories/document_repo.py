from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus


class DocumentRepository:
    def get_by_id(self, db: Session, doc_id: int, user_id: int):
        return (
            db.query(Document)
            .filter(Document.id == doc_id, Document.user_id == user_id)
            .first()
        )

    def get_all_by_user(self, db: Session, user_id: int):
        return (
            db.query(Document)
            .filter(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .all()
        )

    def create(self, db: Session, **kwargs):
        db_obj = Document(**kwargs)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_status(
        self,
        db: Session,
        db_obj: Document,
        status: DocumentStatus,
        signed_path: str = None,
        signed_hash: str = None,
    ):
        db_obj.status = status
        if signed_path:
            db_obj.signed_file_path = signed_path
        if signed_hash:
            db_obj.signed_file_hash = signed_hash

        db.commit()
        db.refresh(db_obj)
        return db_obj


document_repo = DocumentRepository()

from sqlalchemy.orm import Session
from app.models.certificate import Certificate


class CertificateRepository:
    def get_by_id(self, db: Session, cert_id: int):
        return db.query(Certificate).filter(Certificate.id == cert_id).first()

    def get_by_key_id(self, db: Session, key_id: int):
        return db.query(Certificate).filter(Certificate.key_id == key_id).first()

    def get_by_name(self, db: Session, name: str):
        return db.query(Certificate).filter(Certificate.cert_name == name).first()

    def create(self, db: Session, **kwargs):
        db_obj = Certificate(**kwargs)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


certificate_repo = CertificateRepository()

import hashlib
import asyncio
from types import SimpleNamespace

import pytest

from app.services.file_service import FileService


class DummyUploadFile:
    """
    Minimal UploadFile-like object for deterministic unit tests.
    Giúp test không phụ thuộc vào fastapi.UploadFile thực tế.
    """

    def __init__(self, filename: str, content_type: str, content: bytes):
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self, size: int = -1) -> bytes:
        return self._content


@pytest.mark.unit
def test_upload_document_hash_and_size_are_computed(monkeypatch):
    """
    Validates: FileService tính toán chính xác sha256 hash và file_size
    dựa trên bytes đọc được từ file upload.
    """
    created_db_record = {}

    async def fake_save_file(content: bytes, filename: str, content_type: str) -> str:
        assert content == b"ABC"
        assert content_type == "application/pdf"
        return f"local:/tmp/{filename}"

    def fake_doc_create(db, **kwargs):
        created_db_record.update(kwargs)
        return SimpleNamespace(**kwargs, id=1)

    monkeypatch.setattr("app.services.file_service.save_file", fake_save_file)
    monkeypatch.setattr(
        "app.services.file_service.document_repo.create", fake_doc_create
    )

    svc = FileService()
    f = DummyUploadFile("doc.pdf", "application/pdf", b"ABC")
    doc = asyncio.run(svc.upload_document(db=None, user_id=10, file=f))

    assert doc.user_id == 10
    assert created_db_record["file_size"] == 3
    assert created_db_record["file_hash"] == hashlib.sha256(b"ABC").hexdigest()
    assert created_db_record["mime_type"] == "application/pdf"
    assert created_db_record["file_name"] == "doc.pdf"


@pytest.mark.unit
def test_upload_document_empty_file_edge_case(monkeypatch):
    """
    Validates: Xử lý an toàn file rỗng (0 bytes upload).
    Đảm bảo sinh ra sha256 của chuỗi rỗng và size=0.
    """
    created_db_record = {}

    async def fake_save_file(content: bytes, filename: str, content_type: str) -> str:
        return f"local:/tmp/{filename}"

    def fake_doc_create(db, **kwargs):
        created_db_record.update(kwargs)
        return SimpleNamespace(**kwargs, id=1)

    monkeypatch.setattr("app.services.file_service.save_file", fake_save_file)
    monkeypatch.setattr(
        "app.services.file_service.document_repo.create", fake_doc_create
    )

    svc = FileService()
    f = DummyUploadFile("empty.pdf", "application/pdf", b"")
    asyncio.run(svc.upload_document(db=None, user_id=1, file=f))

    assert created_db_record["file_size"] == 0
    assert created_db_record["file_hash"] == hashlib.sha256(b"").hexdigest()

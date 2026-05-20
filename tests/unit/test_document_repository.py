from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.asyncio

from app.repositories.document_repo import DocumentRepository


@pytest.fixture()
def document_repo_instance():
    return DocumentRepository()


class TestDocumentRepository:
    async def test_create_valid_payload_persists_and_returns_entity(
        self, document_repo_instance, monkeypatch
    ):
        # Arrange
        added = {}

        class DummyDB:
            def add(self, obj):
                added["obj"] = obj

            async def flush(self):
                added["flush"] = True

        monkeypatch.setattr(
            "app.repositories.document_repo.Document",
            lambda **kwargs: SimpleNamespace(**kwargs),
        )
        db = DummyDB()

        # Act
        doc = await document_repo_instance.create(
            db,
            user_id=1,
            file_name="a.pdf",
            original_file_path="local:/a.pdf",
            file_size=10,
            file_hash="h",
            mime_type="application/pdf",
        )

        # Assert
        assert doc.file_name == "a.pdf"
        assert added["obj"] == doc
        assert added["flush"] is True

    async def test_get_by_id_not_found_returns_none(self, document_repo_instance):
        # Arrange
        db = SimpleNamespace(
            execute=lambda stmt: None,
        )
        async def _execute(stmt):
            return SimpleNamespace(scalar_one_or_none=lambda: None)
        db.execute = _execute

        # Act
        result = await document_repo_instance.get_by_id(db, doc_id=999, user_id=1)

        # Assert
        assert result is None

    async def test_update_status_with_signed_path_updates_fields_and_commits(
        self, document_repo_instance
    ):
        # Arrange
        db_obj = SimpleNamespace(
            status=None, signed_file_path=None, signed_file_hash=None
        )
        calls = {"flush": 0}

        class DummyDB:
            async def flush(self):
                calls["flush"] += 1

        db = DummyDB()

        # Act
        out = await document_repo_instance.update_status(
            db=db,
            db_obj=db_obj,
            status="SIGNED",
            signed_path="local:/signed.pdf",
            signed_hash="abc",
        )

        # Assert
        assert out is db_obj
        assert db_obj.status == "SIGNED"
        assert db_obj.signed_file_path == "local:/signed.pdf"
        assert db_obj.signed_file_hash == "abc"
        assert calls["flush"] == 1

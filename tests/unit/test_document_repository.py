from types import SimpleNamespace

import pytest

from app.repositories.document_repo import DocumentRepository


@pytest.fixture()
def document_repo_instance():
    return DocumentRepository()


class TestDocumentRepository:
    def test_create_valid_payload_persists_and_returns_entity(
        self, document_repo_instance, monkeypatch
    ):
        # Arrange
        added = {}

        class DummyDB:
            def add(self, obj):
                added["obj"] = obj

            def commit(self):
                added["commit"] = True

            def refresh(self, obj):
                added["refresh"] = obj

        monkeypatch.setattr(
            "app.repositories.document_repo.Document",
            lambda **kwargs: SimpleNamespace(**kwargs),
        )
        db = DummyDB()

        # Act
        doc = document_repo_instance.create(
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
        assert added["commit"] is True
        assert added["refresh"] == doc

    def test_get_by_id_not_found_returns_none(self, document_repo_instance):
        # Arrange
        class DummyQuery:
            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return None

        db = SimpleNamespace(query=lambda model: DummyQuery())

        # Act
        result = document_repo_instance.get_by_id(db, doc_id=999, user_id=1)

        # Assert
        assert result is None

    def test_update_status_with_signed_path_updates_fields_and_commits(
        self, document_repo_instance
    ):
        # Arrange
        db_obj = SimpleNamespace(
            status=None, signed_file_path=None, signed_file_hash=None
        )
        calls = {"commit": 0, "refresh": 0}

        class DummyDB:
            def commit(self):
                calls["commit"] += 1

            def refresh(self, obj):
                calls["refresh"] += 1

        db = DummyDB()

        # Act
        out = document_repo_instance.update_status(
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
        assert calls["commit"] == 1
        assert calls["refresh"] == 1

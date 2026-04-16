import asyncio
import io

import pytest

import app.utils.file_utils as file_utils


class TestFileUtils:
    def test_get_signed_file_path_local_prefix_returns_local_path(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(
            "app.utils.file_utils.datetime",
            type(
                "D",
                (),
                {
                    "now": staticmethod(
                        lambda: type(
                            "T", (), {"strftime": lambda self, f: "20260101_000000"}
                        )()
                    )
                },
            ),
        )

        # Act
        out = file_utils.get_signed_file_path("a.pdf", "local:/tmp/a.pdf")

        # Assert
        assert out.startswith("local:")
        assert "signed_a_20260101_000000.pdf" in out

    def test_get_file_content_local_reads_bytes(self, monkeypatch):
        # Arrange
        monkeypatch.setattr("builtins.open", lambda *args, **kwargs: io.BytesIO(b"abc"))

        # Act
        content = file_utils.get_file_content("local:/tmp/a.pdf")

        # Assert
        assert content == b"abc"

    def test_get_file_content_cloud_without_supabase_raises(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(file_utils, "USE_SUPABASE", False)

        # Act / Assert
        with pytest.raises(Exception, match="mất kết nối Supabase"):
            file_utils.get_file_content("uploads/a.pdf")

    def test_save_signed_file_content_local_writes_bytes(self, monkeypatch):
        # Arrange
        written = {"data": b""}

        class Writer(io.BytesIO):
            def write(self, data):
                written["data"] = data
                return super().write(data)

        monkeypatch.setattr("builtins.open", lambda *args, **kwargs: Writer())

        # Act
        file_utils.save_signed_file_content("local:/tmp/signed.pdf", b"XYZ")

        # Assert
        assert written["data"] == b"XYZ"

    def test_save_file_local_fallback_writes_content(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(file_utils, "USE_SUPABASE", False)

        class DummyAsyncWriter:
            def __init__(self):
                self.buf = b""

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def write(self, data):
                self.buf += data

        monkeypatch.setattr(
            "app.utils.file_utils.aiofiles.open",
            lambda *args, **kwargs: DummyAsyncWriter(),
        )

        # Act
        out = asyncio.run(file_utils.save_file(b"HELLO", "a.pdf", "application/pdf"))

        # Assert
        assert out.startswith("local:")

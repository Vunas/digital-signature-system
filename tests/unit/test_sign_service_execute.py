from types import SimpleNamespace

import pytest

from app.services.sign_service import SignService


@pytest.fixture()
def sign_data():
    return SimpleNamespace(
        signer_name="Alice",
        signer_reason="Approve",
        signer_location="VN",
    )


class TestSignServiceExecute:
    def test_execute_pdf_signing_tsa_error_fallback_without_tsa(
        self, monkeypatch, sign_data
    ):
        # Arrange
        service = SignService()

        class TempFile:
            def __init__(self, name):
                self.name = name
                self._buf = b""

            def write(self, data):
                self._buf += data

            def flush(self):
                return None

            def close(self):
                return None

        temp_files = [TempFile("in.pdf"), TempFile("out.pdf")]
        monkeypatch.setattr(
            "app.services.sign_service.tempfile.NamedTemporaryFile",
            lambda **kwargs: temp_files.pop(0),
        )
        monkeypatch.setattr(
            "app.services.sign_service.get_file_content", lambda path: b"%PDF-1.4 fake"
        )
        monkeypatch.setattr(
            "app.services.sign_service.signers.SimpleSigner", lambda **kwargs: object()
        )
        monkeypatch.setattr(
            "app.services.sign_service.IncrementalPdfFileWriter",
            lambda *args, **kwargs: object(),
        )
        monkeypatch.setattr(
            "app.services.sign_service.signers.PdfSignatureMetadata",
            lambda **kwargs: object(),
        )

        calls = {"n": 0}

        def fake_sign_pdf(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise Exception("tsa fail")
            return None

        monkeypatch.setattr("app.services.sign_service.signers.sign_pdf", fake_sign_pdf)

        class DummyOpen:
            def __init__(self, mode):
                self.mode = mode

            def __enter__(self):
                class F:
                    def seek(self, *args, **kwargs):
                        return None

                    def read(self):
                        return b"signed"

                    def write(self, data):
                        return len(data)

                return F()

            def __exit__(self, exc_type, exc, tb):
                return False

        monkeypatch.setattr("builtins.open", lambda name, mode: DummyOpen(mode))
        saved = {}
        monkeypatch.setattr(
            "app.services.sign_service.save_signed_file_content",
            lambda path, content: saved.update({"path": path, "content": content}),
        )
        monkeypatch.setattr("app.services.sign_service.os.path.exists", lambda p: True)
        removed = {"count": 0}
        monkeypatch.setattr(
            "app.services.sign_service.os.remove",
            lambda p: removed.__setitem__("count", removed["count"] + 1),
        )

        # Act
        service._execute_pdf_signing(
            input_db_path="local:/in.pdf",
            output_db_path="local:/out.pdf",
            private_key=object(),
            end_entity_cert=object(),
            cert_registry=object(),
            timestamper=object(),
            sign_data=sign_data,
        )

        # Assert
        assert calls["n"] == 2
        assert saved["path"] == "local:/out.pdf"
        assert saved["content"] == b"signed"
        assert removed["count"] == 2

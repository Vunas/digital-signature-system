from types import SimpleNamespace
import builtins

import pytest

from app.services.verify_service import VerifyService


@pytest.mark.unit
def test_verify_pdf_signature_missing_file_raises(monkeypatch):
    # Validates: hard failure when file path doesn't exist.
    svc = VerifyService()
    # Avoid relying on real filesystem state.
    import app.services.verify_service as vs_mod

    monkeypatch.setattr(vs_mod.os.path, "exists", lambda p: False)
    with pytest.raises(FileNotFoundError):
        svc.verify_pdf_signature(db=None, file_path="does-not-exist.pdf")


@pytest.mark.unit
def test_verify_pdf_signature_empty_file_returns_message(monkeypatch):
    # Validates: 0-byte PDF returns a deterministic "empty file" response.
    svc = VerifyService()

    monkeypatch.setattr("app.services.verify_service.os.path.exists", lambda p: True)
    monkeypatch.setattr("app.services.verify_service.os.path.getsize", lambda p: 0)

    res = svc.verify_pdf_signature(db=None, file_path="x.pdf")
    assert res["is_valid"] is False
    assert "rỗng" in res["message"]


@pytest.mark.unit
def test_verify_pdf_signature_no_root_ca_returns_message(monkeypatch):
    # Validates: if no trust roots in DB, verification short-circuits with guidance.
    svc = VerifyService()

    monkeypatch.setattr("app.services.verify_service.os.path.exists", lambda p: True)
    monkeypatch.setattr("app.services.verify_service.os.path.getsize", lambda p: 10)

    class DummyQuery:
        def filter(self, *args, **kwargs):
            return self

        def all(self):
            return []

    db = SimpleNamespace(query=lambda model: DummyQuery())

    # Avoid touching filesystem; VerifyService won't open when roots are missing.
    res = svc.verify_pdf_signature(db=db, file_path="x.pdf")
    assert res["is_valid"] is False
    assert "Root CA" in res["message"]


@pytest.mark.unit
def test_verify_pdf_signature_invalid_signature_result(monkeypatch):
    # Validates: invalid/tampered signature maps to is_valid=False.
    svc = VerifyService()

    monkeypatch.setattr("app.services.verify_service.os.path.exists", lambda p: True)
    monkeypatch.setattr("app.services.verify_service.os.path.getsize", lambda p: 10)

    root_record = SimpleNamespace(certificate_data=b"DERROOT")

    class DummyQuery:
        def __init__(self, rows):
            self._rows = rows

        def filter(self, *args, **kwargs):
            return self

        def all(self):
            return self._rows

    # First query (roots) -> [root_record], second query (intermediates) -> []
    calls = {"n": 0}

    def fake_query(model):
        calls["n"] += 1
        return DummyQuery([root_record] if calls["n"] == 1 else [])

    db = SimpleNamespace(query=fake_query)

    # Mock cert loading and validation context to avoid asn1crypto internals.
    monkeypatch.setattr(
        "app.services.verify_service.ValidationContext",
        lambda trust_roots, other_certs: object(),
    )
    monkeypatch.setattr(
        "app.services.verify_service.x509.Certificate.load",
        lambda b: object(),
    )

    class DummyPdfReader:
        def __init__(self, *args, **kwargs):
            self.embedded_signatures = [SimpleNamespace(sig_object={})]

    monkeypatch.setattr("app.services.verify_service.PdfFileReader", DummyPdfReader)

    dummy_status = SimpleNamespace(
        valid=False,
        intact=False,
        coverage=SimpleNamespace(name="ENTIRE_FILE"),
        timestamp_validity=None,
    )
    monkeypatch.setattr(
        "app.services.verify_service.validation.validate_pdf_signature",
        lambda *args, **kwargs: dummy_status,
    )

    # Mock open() used by VerifyService
    class DummyOpen:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(builtins, "open", lambda *a, **k: DummyOpen())

    res = svc.verify_pdf_signature(db=db, file_path="x.pdf")
    assert res["is_valid"] is False
    assert "KHÔNG HỢP LỆ" in res["message"]

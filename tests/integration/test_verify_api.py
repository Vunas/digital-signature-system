import io
import builtins

import pytest


@pytest.mark.integration
def test_verify_endpoint_rejects_non_pdf(client_full):
    # Validates: content-type gate rejects non-PDF uploads.
    res = client_full.post(
        "/api/verify/pdf",
        files={"file": ("x.txt", b"hi", "text/plain")},
    )
    assert res.status_code == 400


@pytest.mark.integration
def test_verify_endpoint_calls_service_and_returns_payload(monkeypatch, client_full):
    # Validates: route stores upload then calls VerifyService; mocked to keep deterministic.
    monkeypatch.setattr(
        "app.routers.verify_router.verify_service.verify_pdf_signature",
        lambda db, path: {"is_valid": False, "message": "invalid", "signer_info": None},
    )

    # Avoid real filesystem by mocking open/copy/remove/exists at router layer.
    monkeypatch.setattr("app.routers.verify_router.os.path.exists", lambda p: True)
    monkeypatch.setattr("app.routers.verify_router.os.remove", lambda p: None)
    monkeypatch.setattr(builtins, "open", lambda *a, **k: io.BytesIO())
    monkeypatch.setattr(
        "app.routers.verify_router.shutil.copyfileobj",
        lambda src, dst: dst.write(src.read()),
    )

    res = client_full.post(
        "/api/verify/pdf",
        files={"file": ("doc.pdf", b"%PDF-1.4\n%", "application/pdf")},
    )
    assert res.status_code == 200, res.text
    assert res.json()["message"] == "invalid"

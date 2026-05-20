from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.integration
async def test_sign_endpoint_returns_signature_response_shape(
    client_full, fastapi_app_full, override_current_user_full, monkeypatch
):
    # Validates: /api/signatures/sign-pdf uses dependency overrides and returns response.
    async def fake_sign_pdf(db, user_id: int, sign_data):
        assert user_id == override_current_user_full.id
        return SimpleNamespace(
            id=1,
            document_id=sign_data.document_id,
            user_id=user_id,
            hash_algorithm="SHA-256",
            signature_algorithm="RSA",
            signer_name=sign_data.signer_name,
            signer_reason=sign_data.signer_reason,
            signer_location=sign_data.signer_location,
            created_at="2026-01-01T00:00:00Z",
        )

    monkeypatch.setattr(
        "app.routers.signature_router.sign_service.sign_pdf", fake_sign_pdf
    )

    payload = {
        "document_id": 1,
        "key_id": 2,
        "signer_name": "Test Signer",
        "signer_reason": "Reason",
        "signer_location": "VN",
        "visible_signature": True,
        "passphrase": None,
        "raw_private_key": None,
    }

    res = await client_full.post("/api/signatures/sign-pdf", json=payload)
    assert res.status_code == 200, res.text
    body = res.json()

    assert body["document_id"] == 1
    assert body["user_id"] == override_current_user_full.id
    assert body["signature_algorithm"] == "RSA"

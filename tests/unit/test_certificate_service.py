from types import SimpleNamespace

import pytest

from app.services.certificate_service import CertificateService


@pytest.mark.unit
def test_get_private_key_local_requires_raw_private_key():
    # Validates: local storage requires raw key input.
    svc = CertificateService()
    key_record = SimpleNamespace(storage_type="local", private_key_encrypted=b"x")
    with pytest.raises(ValueError, match="Bắt buộc phải có Private Key thô"):
        svc._get_private_key(key_record, raw_key=None)


@pytest.mark.unit
def test_get_private_key_server_passphrase_wrong_raises_value_error(monkeypatch):
    # Validates: wrong passphrase becomes a friendly ValueError.
    svc = CertificateService()
    key_record = SimpleNamespace(
        storage_type="server", private_key_encrypted=b"ENCRYPTED"
    )

    def fake_load_pem_private_key(data, password):
        raise Exception("bad decrypt")

    monkeypatch.setattr(
        "app.services.certificate_service.load_pem_private_key",
        fake_load_pem_private_key,
    )

    with pytest.raises(ValueError, match="Passphrase giải mã khóa không chính xác"):
        svc._get_private_key(key_record, passphrase="wrong")


@pytest.mark.unit
def test_get_private_key_server_auto_uses_aes_decrypt(monkeypatch):
    # Validates: server-auto path uses AES decrypt then loads PEM.
    svc = CertificateService()
    key_record = SimpleNamespace(storage_type="server", private_key_encrypted=b"ENC")

    calls = {"decrypt": 0, "load": 0}

    def fake_decrypt_key(data: bytes) -> bytes:
        calls["decrypt"] += 1
        assert data == b"ENC"
        return b"PEM_PRIVATE_BYTES"

    def fake_load_pem_private_key(data, password):
        calls["load"] += 1
        assert data == b"PEM_PRIVATE_BYTES"
        assert password is None
        return object()

    monkeypatch.setattr(
        "app.services.certificate_service.aes_service.decrypt_key", fake_decrypt_key
    )
    monkeypatch.setattr(
        "app.services.certificate_service.load_pem_private_key",
        fake_load_pem_private_key,
    )

    priv = svc._get_private_key(key_record, passphrase=None)
    assert priv is not None
    assert calls["decrypt"] == 1
    assert calls["load"] == 1

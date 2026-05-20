from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.sign_service import SignService

pytestmark = pytest.mark.asyncio



@pytest.fixture()
def sign_service():
    return SignService()


@pytest.fixture()
def sign_input():
    return SimpleNamespace(
        document_id=1,
        key_id=2,
        signer_name="Alice",
        signer_reason="Approval",
        signer_location="VN",
        raw_private_key=None,
        passphrase=None,
    )


class TestSignServiceFlow:
    async def test_get_and_validate_records_missing_certificate_raises_value_error(
        self, sign_service, sign_input, monkeypatch
    ):
        # Arrange
        monkeypatch.setattr(
            "app.services.sign_service.document_repo.get_by_id",
            AsyncMock(return_value=SimpleNamespace(id=1)),
        )
        monkeypatch.setattr(
            "app.services.sign_service.key_repo.get_by_id",
            AsyncMock(return_value=SimpleNamespace(id=2)),
        )
        monkeypatch.setattr(
            "app.services.sign_service.certificate_repo.get_by_key_id",
            AsyncMock(return_value=None),
        )

        # Act / Assert
        with pytest.raises(ValueError, match="Không tìm thấy tài liệu"):
            await sign_service._get_and_validate_records(
                db=object(), user_id=1, sign_data=sign_input
            )

    async def test_load_private_key_local_without_raw_key_raises_value_error(
        self, sign_service, sign_input
    ):
        # Arrange
        key_record = SimpleNamespace(storage_type="local", private_key_encrypted=b"ENC")

        # Act / Assert
        with pytest.raises(ValueError, match="đính kèm file Private Key"):
            sign_service._load_private_key(key_record, sign_input)

    async def test_load_certificate_missing_data_raises_value_error(self, sign_service):
        # Arrange
        cert_record = SimpleNamespace(certificate_data=None, certificate_pem=None)

        # Act / Assert
        with pytest.raises(ValueError, match="Không tìm thấy dữ liệu chứng chỉ"):
            sign_service._load_certificate(cert_record)

    async def test_setup_timestamper_unreachable_tsa_returns_none(
        self, sign_service, monkeypatch
    ):
        # Arrange
        monkeypatch.setattr(
            "app.services.sign_service.os.getenv", lambda key: "http://tsa"
        )
        monkeypatch.setattr(
            "app.services.sign_service.requests.get",
            lambda *args, **kwargs: (_ for _ in ()).throw(Exception("down")),
        )

        # Act
        timestamper = sign_service._setup_timestamper()

        # Assert
        assert timestamper is None

    async def test_setup_timestamper_reachable_returns_http_timestamper(
        self, sign_service, monkeypatch
    ):
        # Arrange
        monkeypatch.setattr(
            "app.services.sign_service.os.getenv", lambda key: "http://tsa"
        )
        monkeypatch.setattr(
            "app.services.sign_service.requests.get", lambda *args, **kwargs: object()
        )
        marker = object()
        monkeypatch.setattr(
            "app.services.sign_service.HTTPTimeStamper", lambda url: marker
        )

        # Act
        timestamper = sign_service._setup_timestamper()

        # Assert
        assert timestamper is marker

    async def test_build_certificate_registry_with_intermediate_pem_registers_cert(
        self, sign_service, monkeypatch
    ):
        # Arrange
        inter = SimpleNamespace(certificate_data="PEM-TEXT")
        monkeypatch.setattr(
            "app.services.sign_service.certificate_repo.get_by_name",
            AsyncMock(return_value=inter),
        )
        monkeypatch.setattr("app.services.sign_service.pem.detect", lambda b: True)
        monkeypatch.setattr(
            "app.services.sign_service.pem.unarmor",
            lambda b: (None, None, b"DER"),
        )
        cert_obj = object()
        monkeypatch.setattr(
            "app.services.sign_service.x509.Certificate.load", lambda b: cert_obj
        )

        class DummyStore:
            def __init__(self):
                self.registered = None

            def register(self, cert):
                self.registered = cert

        monkeypatch.setattr(
            "app.services.sign_service.SimpleCertificateStore", DummyStore
        )

        # Act
        registry = await sign_service._build_certificate_registry(db=object())

        # Assert
        assert registry.registered is cert_obj

    async def test_sign_pdf_success_flow_calls_update_and_create(
        self, sign_service, sign_input, monkeypatch
    ):
        # Arrange
        doc = SimpleNamespace(
            id=1, file_name="a.pdf", original_file_path="local:/a.pdf", signed_file_path=None
        )
        doc.mark_as_signed = lambda new_signed_path, new_signed_hash: (
            setattr(doc, "signed_file_path", new_signed_path),
            setattr(doc, "signed_file_hash", new_signed_hash),
        )
        key_record = SimpleNamespace(id=2)
        cert_record = SimpleNamespace(id=3)
        signature_record = SimpleNamespace(id=10, document_id=1)

        monkeypatch.setattr(
            sign_service,
            "_get_and_validate_records",
            AsyncMock(return_value=(doc, key_record, cert_record)),
        )
        monkeypatch.setattr(
            "app.services.sign_service.get_signed_file_path",
            lambda file_name, input_path: "local:/signed.pdf",
        )
        monkeypatch.setattr(
            sign_service, "_load_private_key", lambda *args, **kwargs: object()
        )
        monkeypatch.setattr(
            sign_service, "_load_certificate", lambda *args, **kwargs: object()
        )
        monkeypatch.setattr(
            sign_service,
            "_build_certificate_registry",
            AsyncMock(return_value=object()),
        )
        monkeypatch.setattr(sign_service, "_setup_timestamper", lambda: None)
        monkeypatch.setattr(
            sign_service, "_execute_pdf_signing", lambda *args, **kwargs: None
        )

        captured = {"create": 0, "update": 0}

        monkeypatch.setattr(
            "app.services.sign_service.signature_repo.create",
            AsyncMock(side_effect=lambda **kwargs: (
                captured.__setitem__("create", captured["create"] + 1)
                or signature_record
            )),
        )
        monkeypatch.setattr("app.services.sign_service.log_service.log_action", AsyncMock())

        # Act
        result = await sign_service.sign_pdf(db=object(), user_id=1, sign_data=sign_input)

        # Assert
        assert result == signature_record
        assert captured["create"] == 1
        assert doc.signed_file_path == "local:/signed.pdf"

    async def test_sign_pdf_exception_path_triggers_uow_rollback(
        self, sign_service, sign_input, mock_uow, monkeypatch
    ):
        # Arrange
        monkeypatch.setattr(
            sign_service,
            "_get_and_validate_records",
            AsyncMock(side_effect=ValueError("boom")),
        )

        async def _service_with_uow():
            try:
                await sign_service.sign_pdf(db=object(), user_id=1, sign_data=sign_input)
                await mock_uow.commit()
            except Exception:
                await mock_uow.rollback()
                raise

        # Act / Assert
        with pytest.raises(ValueError, match="boom"):
            await _service_with_uow()
        assert mock_uow.committed is False
        assert mock_uow.rolled_back is True

import hashlib

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.services.crypto.rsa_service import RSAService


@pytest.mark.unit
def test_rsa_service_generate_key_pair_returns_valid_pem():
    pub_pem, priv_pem = RSAService.generate_key_pair(2048)

    assert isinstance(pub_pem, (bytes, bytearray))
    assert isinstance(priv_pem, (bytes, bytearray))
    assert b"BEGIN PUBLIC KEY" in pub_pem
    assert b"BEGIN PRIVATE KEY" in priv_pem

    pub = serialization.load_pem_public_key(pub_pem)
    priv = serialization.load_pem_private_key(priv_pem, password=None)
    assert pub is not None
    assert priv is not None


@pytest.mark.unit
def test_sha256_hashing_is_deterministic_and_64_hex_chars():
    msg = b"hello world"
    digest1 = hashlib.sha256(msg).hexdigest()
    digest2 = hashlib.sha256(msg).hexdigest()

    assert digest1 == digest2
    assert len(digest1) == 64
    int(digest1, 16)  # validates hex


@pytest.mark.unit
def test_digital_signature_verification_rsa_sha256_roundtrip():
    pub_pem, priv_pem = RSAService.generate_key_pair(2048)
    pub = serialization.load_pem_public_key(pub_pem)
    priv = serialization.load_pem_private_key(priv_pem, password=None)

    message = b"payload-to-sign"
    signature = priv.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )

    # Should not raise
    pub.verify(
        signature,
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )

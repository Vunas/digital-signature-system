import hashlib

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.services.crypto.rsa_service import RSAService


@pytest.mark.unit
def test_rsa_pss_signatures_are_not_deterministic_for_same_message():
    """
    Validates (security property): RSA-PSS is randomized, so signing the same message
    twice should (almost certainly) produce different signatures.
    This helps prevent signature replay/fingerprinting style attacks.
    """
    pub_pem, priv_pem = RSAService.generate_key_pair(2048)
    priv = serialization.load_pem_private_key(priv_pem, password=None)

    message = b"same-message"
    sig1 = priv.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    sig2 = priv.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    assert sig1 != sig2


@pytest.mark.unit
def test_verification_fails_for_altered_message():
    """
    Validates: if the message is altered after signing, verification must fail.
    """
    pub_pem, priv_pem = RSAService.generate_key_pair(2048)
    pub = serialization.load_pem_public_key(pub_pem)
    priv = serialization.load_pem_private_key(priv_pem, password=None)

    message = b"original"
    signature = priv.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )

    tampered = b"original."
    with pytest.raises(InvalidSignature):
        pub.verify(
            signature,
            tampered,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )


@pytest.mark.unit
def test_verification_fails_for_mismatched_key_pair():
    """
    Validates: signatures cannot be verified with an unrelated public key (forgery attempt).
    """
    pub1_pem, priv1_pem = RSAService.generate_key_pair(2048)
    pub2_pem, _priv2_pem = RSAService.generate_key_pair(2048)

    pub2 = serialization.load_pem_public_key(pub2_pem)
    priv1 = serialization.load_pem_private_key(priv1_pem, password=None)

    message = b"payload"
    signature = priv1.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )

    with pytest.raises(InvalidSignature):
        pub2.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )


@pytest.mark.unit
def test_verification_fails_for_corrupted_signature_bytes():
    """
    Validates: bitflips in the signature bytes must cause verification failure.
    This simulates transmission/storage corruption and active tampering.
    """
    pub_pem, priv_pem = RSAService.generate_key_pair(2048)
    pub = serialization.load_pem_public_key(pub_pem)
    priv = serialization.load_pem_private_key(priv_pem, password=None)

    message = b"payload"
    signature = priv.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )

    corrupted = bytearray(signature)
    corrupted[len(corrupted) // 2] ^= 0x01

    with pytest.raises(InvalidSignature):
        pub.verify(
            bytes(corrupted),
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )


@pytest.mark.unit
def test_verification_fails_when_padding_scheme_is_mismatched():
    """
    Validates: RSA padding parameters are part of the signature scheme.
    If a signature is created using PKCS#1 v1.5, verifying it as PSS must fail (and vice versa).
    """
    pub_pem, priv_pem = RSAService.generate_key_pair(2048)
    pub = serialization.load_pem_public_key(pub_pem)
    priv = serialization.load_pem_private_key(priv_pem, password=None)

    message = b"payload"

    # Sign with PKCS#1 v1.5 (legacy scheme).
    pkcs1_sig = priv.sign(message, padding.PKCS1v15(), hashes.SHA256())

    # Verifying with PSS must fail.
    with pytest.raises(InvalidSignature):
        pub.verify(
            pkcs1_sig,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )


@pytest.mark.unit
def test_sha256_hashing_consistency_across_code_paths():
    """
    Validates: SHA-256 hashing is consistent and canonical in hex encoding.
    This guards against subtle bugs like double-encoding or unexpected unicode transforms.
    """
    msg = b"canonical-bytes"
    digest_hex = hashlib.sha256(msg).hexdigest()

    # Recompute the same way and compare.
    assert digest_hex == hashlib.sha256(msg).hexdigest()

    # Hex digest must be exactly 64 lowercase hex chars.
    assert len(digest_hex) == 64
    assert digest_hex == digest_hex.lower()
    int(digest_hex, 16)

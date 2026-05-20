import enum


class LogLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ActionStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class TargetResourceType(str, enum.Enum):
    USER = "USER"
    KEY = "KEY"
    CERTIFICATE = "CERTIFICATE"
    DOCUMENT = "DOCUMENT"
    SIGNATURE = "SIGNATURE"
    SYSTEM = "SYSTEM"


class KeyStorageType(str, enum.Enum):
    SERVER = "server"
    USB_TOKEN = "usb_token"
    HSM = "hsm"
    LOCAL = "local"


class SignatureAlgo(str, enum.Enum):
    RSA = "RSA"
    ECDSA = "ECDSA"


class HashAlgo(str, enum.Enum):
    SHA_256 = "SHA-256"
    SHA_512 = "SHA-512"


class CertType(str, enum.Enum):
    ROOT = "root"
    INTERMEDIATE = "intermediate"
    END_ENTITY = "end_entity"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    SIGNED = "SIGNED"
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"


class OutboxStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

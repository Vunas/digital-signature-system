<div align="center">

# 🔐 SECURESIGN

### PAdES Digital Signature Platform

**Enterprise-grade PKI & Secure PDF Signing System**

<img src="./docs/img/1.png" width="85%" />

</div>

---

## 📖 About The Project

**SecureSign** is a production-ready digital signature platform that simulates a complete **Public Key Infrastructure (PKI)** system.

It enables secure document signing using industry standards such as **RSA, X.509, and PAdES**, ensuring authenticity, integrity, and non-repudiation.

### 🔑 Core Capabilities

* RSA key pair generation & secure storage
* X.509 certificate chain (Root → Intermediate → End-user)
* Embedded **PAdES digital signatures** inside PDF
* RFC3161 compliant **Timestamp Authority (TSA)**
* Cryptographic verification & tamper detection

---

## ✨ Key Features

### 🔐 Key & Certificate Management

* RSA 2048 / 4096 key generation
* Internal Certificate Authority (CA)
* AES-encrypted private key storage
* Export `.pem` keys for local usage

---

### 📄 PDF Digital Signing (PAdES)

* Real PDF signing (NOT just hashing)
* ASN.1 / DER signature embedding
* Visible signature support
* Compatible with Adobe Acrobat & Foxit Reader

---

### ⏱️ Timestamping (TSA)

* RFC3161 compliant timestamps
* Prevents backdating attacks
* Enables Long-Term Validation (LTV)

---

### 🛡️ Security & Integrity

* SHA-256 hashing
* RSA-PSS digital signatures
* Detects any document modification
* Immediate signature invalidation if tampered

---

### 💻 User Interface

* Responsive dashboard (Tailwind CSS)
* Drag & drop PDF upload
* Real-time signing feedback

---

## 📸 Screenshots

   <p align="center">
   <img src="./docs/img/2.png" width="45%" />
   <img src="./docs/img/3.png" width="45%" />
   </p>

   <p align="center">
   <img src="./docs/img/4.png" width="45%" />
   <img src="./docs/img/5.png" width="45%" />
   </p>

---

## 🧠 Technical Highlights

* Full PKI system (not mock implementation)
* Internal Certificate Authority (Root + Intermediate)
* Internal Time Stamping Authority
* X.509 & ASN.1 certificate processing
* Secure private key lifecycle (AES encryption)
* PAdES-B-LT compatible signature workflow

---

## 🛠️ Tech Stack

### Backend

* FastAPI
* SQLAlchemy
* PostgreSQL

### Security & Cryptography

* pyHanko
* cryptography
* asn1crypto

### Frontend

* Tailwind CSS
* Vanilla JavaScript (Fetch API)

---

## 🧪 Testing

Run all tests:

```bash
python -m pytest
```

### ✔ Coverage includes:

* Unit tests (crypto, key service, signing logic)
* Integration tests (API endpoints)
* Security tests (RSA signing & verification)

### ✔ Testing setup:

* SQLite in-memory database
* FastAPI dependency override
* Isolated transactional tests

---

## 🚀 Getting Started

### 1. Clone repository

```bash
git clone https://github.com/your-username/securesign.git
cd securesign
```

---

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Setup environment

Create `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/digital_signature_db
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-32-byte-aes-key
```

---

### 5. Seed database

```bash
python -m app.db.seed.seed_data --force
```

---

### 6. Run server

```bash
uvicorn app.main:app --reload
```

👉 Open: http://localhost:8000

---

## 🐳 Docker (Recommended)

```bash
docker compose up --build
```

This will start:

* FastAPI backend
* PostgreSQL database

---

## 👥 Demo Accounts

| Username       | Role     | Description                   |
| -------------- | -------- | ----------------------------- |
| admin          | Admin    | Full system control (Root CA) |
| demo           | User     | Ready to sign documents       |
| user0 -> 9     | User     | Ready to sign documents       |

**Password:** `123456`

---

## 💡 Usage Workflow

1. Login
2. Generate key pair
3. Upload PDF
4. Sign document
5. Download signed file
6. Verify signature

---

## ✅ Trusted Validation (IMPORTANT)

To display **"Trusted Signature"** in Adobe Acrobat:

1. Download Root CA certificate
2. Import into:

   * Windows Trust Store
   * macOS Keychain
   * Adobe Trusted Certificates

---

## 🔒 Security Notes

* Private keys are encrypted using AES before storage
* RSA keys are never stored in plaintext
* Signatures use SHA-256 + RSA-PSS
* Timestamping prevents replay attacks
* Full certificate chain validation supported

---

## 🎯 Real-World Applications

* Banking & Finance
* Healthcare
* Government
* Enterprise contracts

---

<div align="center">

**Built with ❤️ for Secure Digital Transactions | 2026**

</div>

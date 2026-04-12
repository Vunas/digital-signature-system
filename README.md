<div align="center">

# 🔐 SECURESIGN

### PAdES Digital Signature Platform

**Enterprise-grade PKI & Secure PDF Signing System**

![Dashboard](./docs/dashboard.png)

</div>

---

## 📖 About The Project

**SecureSign** is a production-ready digital signature platform that simulates a full **Public Key Infrastructure (PKI)** workflow.

The system enables:

* 🔑 RSA key generation & secure storage
* 📜 X.509 certificate issuance (Root → Intermediate → User)
* 📄 Native PAdES digital signatures embedded directly into PDF files
* ⏱️ Trusted timestamping (RFC3161)

All signed documents are:

✔ Tamper-proof
✔ Cryptographically verifiable
✔ Compatible with Adobe Acrobat & Foxit Reader

---

## ✨ Key Features

### 🔐 Advanced Key & Certificate Management

* RSA 2048/4096 key pair generation
* Internal CA system (Root + Intermediate)
* AES-encrypted private key storage
* Export keys as `.pem` for local custody

---

### 📄 Embedded PAdES Signatures

* Real PDF signing (NOT just hashing)
* ASN.1 / DER signature block embedding
* Visible signature watermark
* Adobe-compatible validation

---

### ⏱️ Time-Stamping Authority (TSA)

* RFC3161 compliant timestamping
* Prevents backdating attacks
* Enables long-term validation (LTV)

---

### 🛡️ Tamper Detection

* SHA-256 integrity verification
* Detects even 1-character modification
* Instant signature invalidation

---

### 💻 Modern UI/UX

* Responsive Dashboard (Tailwind CSS)
* Drag & Drop PDF upload
* Real-time signing status

![Sign Page](./docs/sign.png)

---

## 🧠 Technical Highlights

* Full PKI implementation (not mock)
* Internal Certificate Authority (CA)
* Internal Time Stamping Authority (TSA)
* X.509 / ASN.1 certificate processing
* AES-secured private key lifecycle
* PAdES-B-LT compatible signatures

---

## 🛠️ Tech Stack

### Backend

* FastAPI
* SQLAlchemy
* PostgreSQL

### Security & Crypto

* pyHanko
* cryptography
* asn1crypto

### Frontend

* Tailwind CSS
* Vanilla JavaScript (Fetch API)

---

## 🚀 Getting Started

### 1. Clone project

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

Tạo file `.env`:

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

## 👥 Demo Accounts

| Username       | Role     | Description                    |
| -------------- | -------- | ------------------------------ |
| admin          | Admin    | Full system control (Root CA)  |
| giamdoc_nguyen | Signer   | Has certificate, ready to sign |
| nhanvien_tran  | Employee | Upload & review documents      |

**Password:** `123456`

---

## 💡 Usage Workflow

1. Login
2. Generate key pair
3. Upload PDF
4. Sign document
5. Download signed file
6. Verify in Adobe Acrobat

---

## ✅ Trusted Validation (IMPORTANT)

To see **green "Trusted" checkmark** in Adobe:

1. Download Root CA certificate
2. Import into:

   * Windows Trust Store
   * macOS Keychain
   * Adobe Trusted Certificates

---

## 🎯 Real-World Applications

* 🏦 Banking & Finance
* 🏥 Healthcare
* 🏛️ Government
* 🏢 Enterprise contracts

---

<div align="center">

**Built with ❤️ for Secure Digital Transactions | 2026**

</div>

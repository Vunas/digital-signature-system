pip install -r requirements.txt
uvicorn app.main:app --reload
│
├── app/
│   │
│   ├── main.py                 # Entry point FastAPI
│   │
│   ├── core/                   # Cấu hình & bảo mật
│   │   ├── config.py           # Config (DB URL, SECRET_KEY)
│   │   ├── security.py         # Hash password (bcrypt)
│   │   └── encryption.py       # Encrypt private key (AES)
│   │
│   ├── db/                     # Database
│   │   ├── database.py         # Kết nối PostgreSQL
│   │   └── base.py             # Base model
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py
│   │   ├── key.py
│   │   ├── document.py
│   │   ├── signature.py
│   │   └── log.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── user_schema.py
│   │   ├── key_schema.py
│   │   ├── document_schema.py
│   │   └── signature_schema.py
│   │
│   ├── services/               # BUSINESS LOGIC (quan trọng nhất)
│   │   ├── crypto_service.py   # RSA, SHA-256
│   │   ├── key_service.py      # tạo & quản lý key
│   │   ├── sign_service.py     # ký PDF
│   │   ├── verify_service.py   # xác thực chữ ký
│   │   └── file_service.py     # xử lý upload file
│   │
│   ├── routers/                # API routes
│   │   ├── auth_router.py      # login
│   │   ├── key_router.py       # generate key
│   │   ├── sign_router.py      # ký file
│   │   └── verify_router.py    # verify
│   │
│   ├── templates/              # Jinja2 (UI)
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── generate_key.html
│   │   ├── sign.html
│   │   └── verify.html
│   │
│   ├── static/                 # CSS / JS
│   │   ├── css/
│   │   └── js/
│   │
│   └── utils/                  # helper
│       ├── hash_utils.py
│       ├── file_utils.py
│       └── logger.py
│
├── uploads/                    # Lưu file PDF
│   ├── documents/
│   └── signatures/
│
├── alembic/                   # Migration DB (optional)
│
├── requirements.txt
├── .env
└── README.md
-- =========================
-- USERS
-- =========================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- KEYS (RSA)
-- =========================
CREATE TABLE keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    key_name VARCHAR(100),

    public_key TEXT NOT NULL,
    private_key_encrypted TEXT NOT NULL,

    key_size INTEGER DEFAULT 2048,
    algorithm VARCHAR(50) DEFAULT 'RSA',
    storage_type VARCHAR(20) DEFAULT 'server'

    is_revoked BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- DOCUMENTS
-- =========================
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    file_name VARCHAR(255),
    file_path TEXT,

    file_size INTEGER,
    mime_type VARCHAR(50),

    file_hash TEXT NOT NULL, -- SHA-256

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- SIGNATURES
-- =========================
CREATE TABLE signatures (
    id SERIAL PRIMARY KEY,

    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    key_id INTEGER REFERENCES keys(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),

    signature TEXT NOT NULL, -- base64

    hash_algorithm VARCHAR(50) DEFAULT 'SHA-256',
    signature_algorithm VARCHAR(50) DEFAULT 'RSA',

    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- VERIFY HISTORY (🔥 ĂN ĐIỂM)
-- =========================
CREATE TABLE verify_logs (
    id SERIAL PRIMARY KEY,

    document_id INTEGER REFERENCES documents(id),
    signature_id INTEGER REFERENCES signatures(id),

    is_valid BOOLEAN,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    message TEXT
);

-- =========================
-- AUDIT LOGS
-- =========================
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,

    user_id INTEGER REFERENCES users(id),

    action VARCHAR(50), -- LOGIN, SIGN, VERIFY, GENERATE_KEY
    ip_address VARCHAR(50),

    description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
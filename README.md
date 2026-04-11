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
python -m app.db.seed.seed_data  
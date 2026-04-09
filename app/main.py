from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.core.middleware import LoggingMiddleware
from app.db.database import engine
from app.db.base import Base

# Import models để SQLAlchemy nhận diện và tạo bảng tự động

# Import API Routers
from app.routers import auth_router, key_router, sign_router, document_router, dashboard_router

# 1. TỰ ĐỘNG TẠO BẢNG TRONG DATABASE
# Lệnh này sẽ quét các models và tạo bảng trên PostgreSQL nếu chưa có
Base.metadata.create_all(bind=engine)

# 2. KHỞI TẠO FASTAPI APP
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hệ thống Chữ ký số - Đồ án An Ninh Mạng",
)

# 3. ĐĂNG KÝ MIDDLEWARE (Bảo mật CORS & Ghi Log)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. CẤU HÌNH GIAO DIỆN (UI) VÀ TÀI NGUYÊN TĨNH
# Phục vụ CSS, JS từ thư mục static
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Khởi tạo Jinja2 engine để render HTML
templates = Jinja2Templates(directory="app/templates")

# 5. ĐĂNG KÝ CÁC API ROUTERS
app.include_router(auth_router.router)
app.include_router(key_router.router)
app.include_router(sign_router.router)
app.include_router(document_router.router)
app.include_router(dashboard_router.router)

# ==========================================
# 6. CÁC ROUTES PHỤC VỤ GIAO DIỆN (FRONTEND)
# ==========================================


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """Điều hướng mặc định về trang đăng nhập"""
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    """Trang Đăng Nhập"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request):
    """Trang Tổng Quan (Sau khi đăng nhập)"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/generate-key", response_class=HTMLResponse, include_in_schema=False)
async def generate_key_page(request: Request):
    """Trang Khởi Tạo Khóa"""
    return templates.TemplateResponse("generate_key.html", {"request": request})


@app.get("/sign", response_class=HTMLResponse, include_in_schema=False)
async def sign_page(request: Request):
    """Trang Ký Văn Bản (File bạn vừa đang xem)"""
    return templates.TemplateResponse("sign.html", {"request": request})


@app.get("/verify", response_class=HTMLResponse, include_in_schema=False)
async def verify_page(request: Request):
    """Trang Xác Thực Chữ Ký"""
    return templates.TemplateResponse("verify.html", {"request": request})


# 7. KHỞI CHẠY SERVER BẰNG UVICORN
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

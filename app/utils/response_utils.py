from fastapi.responses import JSONResponse


def success_response(
    data: dict = None, message: str = "Thành công", status_code: int = 200
):
    """Chuẩn hóa cấu trúc trả về của API thành công."""
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": data or {}},
    )


def error_response(message: str = "Đã xảy ra lỗi", status_code: int = 400):
    """Chuẩn hóa cấu trúc trả về của API thất bại."""
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message, "data": None},
    )

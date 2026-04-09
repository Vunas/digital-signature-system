from datetime import datetime
import pytz


def format_datetime_vn(dt: datetime) -> str:
    """Chuyển đổi thời gian UTC trong DB sang giờ Việt Nam (để hiện lên UI)."""
    if dt is None:
        return ""
    # Múi giờ VN là UTC+7
    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")

    # Nếu datetime chưa có timezone (naive), gán nó là UTC trước
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    vn_dt = dt.astimezone(vn_tz)
    return vn_dt.strftime("%d/%m/%Y %H:%M:%S")

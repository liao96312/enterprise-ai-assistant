from fastapi import Header, HTTPException

from app.config import settings


def require_admin(authorization: str = Header(default="")) -> None:
    if not settings.auth_enabled:
        return
    if not settings.admin_token:
        raise HTTPException(status_code=500, detail="AUTH_ENABLED=true but ADMIN_TOKEN is empty.")
    expected = f"Bearer {settings.admin_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="认证失败，请提供有效的 Bearer Token。")

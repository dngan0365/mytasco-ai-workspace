"""
Xác thực demo cho hackathon: đăng nhập chỉ bằng user_id có sẵn trong dataset
(không có mật khẩu thật) rồi phát JWT chứa role/department để các tầng sau
(RBAC, retrieval) dùng làm ngữ cảnh phân quyền.

Trong hệ thống thật, thay bằng JWT do My Tasco COP auth (/cop/auth/auth/...) phát hành,
và chỉ cần đọc claims tương ứng ở get_current_user.
"""
import time

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user: dict) -> str:
    settings = get_settings()
    now = int(time.time())
    payload = {
        "sub": user["user_id"],
        "role": user["role"],
        "department": user["department"],
        "full_name": user.get("full_name"),
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
        ) from exc


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu Bearer token. Gọi POST /auth/login trước.",
        )
    payload = decode_token(creds.credentials)
    return {
        "user_id": payload["sub"],
        "role": payload["role"],
        "department": payload["department"],
        "full_name": payload.get("full_name"),
    }

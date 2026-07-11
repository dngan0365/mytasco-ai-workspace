from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.security import create_access_token
from app.data.loader import get_store

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    user_id: str  # ví dụ "U001" — xem GET /auth/demo-users để lấy danh sách


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    """
    Đăng nhập DEMO: chỉ cần user_id có trong dataset (không mật khẩu).
    Trong hệ thống thật, thay bằng xác thực JWT do My Tasco COP auth phát hành.
    """
    store = get_store()
    user = store.get_user(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_id không tồn tại trong dataset")
    token = create_access_token(user)
    return LoginResponse(access_token=token, user=user)


@router.get("/demo-users")
def demo_users():
    """Danh sách toàn bộ user mẫu (32 user, 4 vai trò) để test nhanh Postman/Swagger."""
    store = get_store()
    return [
        {
            "user_id": u["user_id"],
            "full_name": u["full_name"],
            "role": u["role"],
            "department": u["department"],
        }
        for u in store.users.values()
    ]

from fastapi import APIRouter, Depends, HTTPException

from app.core.rbac import can_access, filter_accessible
from app.core.security import get_current_user
from app.data.loader import get_store

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(user: dict = Depends(get_current_user)):
    """Danh sách tài liệu người dùng hiện tại ĐƯỢC PHÉP xem (đã lọc ACL)."""
    store = get_store()
    accessible = filter_accessible(user, store.list_documents())
    return [{k: v for k, v in d.items() if k != "content_vi"} for d in accessible]


@router.get("/{document_id}")
def get_document(document_id: str, user: dict = Depends(get_current_user)):
    """Xem chi tiết 1 tài liệu — 403 nếu không đủ quyền, 404 nếu không tồn tại."""
    store = get_store()
    doc = store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    if not can_access(user, doc):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: tài liệu này yêu cầu quyền cao hơn hoặc thuộc phòng ban khác",
        )
    return doc

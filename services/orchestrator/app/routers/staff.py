from fastapi import APIRouter, Depends, Query
from mytasco_adapter import MyTascoClient

from app.core.security import get_current_user

router = APIRouter(prefix="/mytasco", tags=["mytasco-tools"])
client = MyTascoClient()


@router.get("/staff/search")
async def staff_search(keyword: str | None = None, user: dict = Depends(get_current_user)):
    """Demo tool-calling: tra cứu nhân viên qua mock COP {sys}/staff/search."""
    return await client.search_staff(keyword=keyword)


@router.get("/requests")
async def list_requests(status: str | None = Query(default=None), user: dict = Depends(get_current_user)):
    """Demo tool-calling: tra cứu đơn từ qua mock COP {hrm}/request/search."""
    return await client.list_requests(status=status)

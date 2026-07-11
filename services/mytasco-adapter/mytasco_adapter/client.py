"""
Thin client adapter gọi COP API của My Tasco (sys/hrm/aiwsp/noti...), theo đúng
path/param/envelope mô tả trong "My Tasco AI Hackathon API Documentation".

Dùng cho mock server (infra/mock-server/mock_mytasco_server.js) lúc dev/demo,
và trỏ thẳng sang gateway COP thật khi tích hợp production — chỉ cần đổi base_url,
không cần sửa code gọi.
"""
from __future__ import annotations

import os

import httpx

DEFAULT_BASE_URL = os.environ.get("MYTASCO_MOCK_BASE_URL", "http://localhost:8788")
APP_CODE_HEADER = {"X-App-Code": "MYTASCO"}


class MyTascoClient:
    """SDK tối giản cho các service Python (orchestrator, ingestion, agent...) gọi API My Tasco."""

    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = base_url or DEFAULT_BASE_URL
        self.timeout = timeout

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, headers=APP_CODE_HEADER) as client:
            resp = await client.get(path, params=params)
            resp.raise_for_status()
            return resp.json()

    async def _post(self, path: str, json: dict) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, headers=APP_CODE_HEADER) as client:
            resp = await client.post(path, json=json)
            resp.raise_for_status()
            return resp.json()

    # ---- 1. Staff directory ----
    async def search_staff(self, keyword: str | None = None, org_unit_id: int | None = None, page_size: int = 20) -> dict:
        example = {k: v for k, v in {"keyword": keyword, "orgUnitId": org_unit_id}.items() if v is not None}
        return await self._post("/staff/search", {"example": example, "pageInfo": {"pageSize": page_size, "currentPage": 0}})

    # ---- 2. AI usage overview ----
    async def ai_usage_overview(self, department_ids: str | None = None) -> dict:
        return await self._get("/ai-usage-overview/general", {"departmentIds": department_ids} if department_ids else None)

    # ---- 3. Organization graph ----
    async def get_org_tree(self) -> dict:
        return await self._get("/organization/tree")

    # ---- 4. Attendance ----
    async def get_attendance(self, staff_id: int, from_date: str, to_date: str) -> dict:
        return await self._get("/attendance/by-staff", {"staffId": staff_id, "fromDate": from_date, "toDate": to_date})

    # ---- 5. Requests & approvals ----
    async def list_requests(self, status: str | None = None, request_type: str | None = None) -> dict:
        example = {k: v for k, v in {"status": status, "requestType": request_type}.items() if v is not None}
        return await self._post("/request/search", {"example": example, "pageInfo": {"pageSize": 20, "currentPage": 0}})

    async def create_request(self, request_type: str, from_date: str, to_date: str, reason: str, staff_id: int) -> dict:
        return await self._post(
            "/request/create",
            {"requestType": request_type, "fromDate": from_date, "toDate": to_date, "reason": reason, "staffId": staff_id},
        )

    async def approve_request(self, request_id: int) -> dict:
        return await self._post("/request/approve", {"id": request_id})

    async def reject_request(self, request_id: int) -> dict:
        return await self._post("/request/reject", {"id": request_id})

    # ---- 6. Payroll (OTP gated) ----
    async def get_payslip(self, month: int, year: int, otp: str | None = None) -> dict:
        params = {"month": month, "year": year}
        if otp:
            params["otp"] = otp
        return await self._get("/salary-staff-payslip/self-by-month", params)

    # ---- 7. News & feed ----
    async def search_news(self, keyword: str | None = None, category_id: int | None = None) -> dict:
        params = {k: v for k, v in {"keyword": keyword, "categoryId": category_id}.items() if v is not None}
        return await self._get("/news-article/search", params)

    # ---- 8. Notifications ----
    async def search_notifications(self, is_read: bool | None = None) -> dict:
        return await self._get("/noti-app/search", {"isRead": is_read} if is_read is not None else None)

    async def mark_notification_read(self, notification_id: int) -> dict:
        return await self._post("/noti-app/mark-read", {"id": notification_id})

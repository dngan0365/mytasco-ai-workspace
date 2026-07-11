"""
OpenAPI-style gateway cho các tool nghiệp vụ My Tasco.

Repo hiện tại chưa có một tool-gateway độc lập, nên module này làm 2 việc:
- xuất một OpenAPI manifest để agent/UI có thể discover các operation;
- map các operation đó sang MyTascoClient trong demo/local.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from mytasco_adapter import MyTascoClient
except ImportError:
    # Fallback khi MyTascoClient không available (e.g., dev environment)
    MyTascoClient = None

OPENAPI_SPEC: dict[str, Any] = {
    "openapi": "3.1.0",
    "info": {
        "title": "My Tasco Enterprise Tool Gateway",
        "version": "1.0.0",
    },
    "paths": {
        "/staff/search": {"post": {"operationId": "search_staff_directory"}},
        "/request/search": {"post": {"operationId": "list_hr_requests"}},
        "/attendance/by-staff": {"get": {"operationId": "get_staff_attendance"}},
        "/salary-staff-payslip/self-by-month": {"get": {"operationId": "get_payslip"}},
        "/news-article/search": {"get": {"operationId": "search_company_news"}},
        "/noti-app/search": {"get": {"operationId": "search_notifications"}},
    },
}


def get_openapi_spec() -> dict[str, Any]:
    return OPENAPI_SPEC


@dataclass(frozen=True)
class OpenAPIRequest:
    operation_id: str
    arguments: dict[str, Any]


class OpenAPIToolGateway:
    def __init__(self, client: MyTascoClient | None = None):
        if client is not None:
            self.client = client
        elif MyTascoClient is not None:
            self.client = MyTascoClient()
        else:
            # Fallback mock implementation for development/testing
            self.client = None
            self._mock_mode = True
            return
        self._mock_mode = False

    async def invoke(self, request: OpenAPIRequest) -> str:
        operation = request.operation_id
        args = request.arguments

        # Nếu ở chế độ mock, trả về response mẫu
        if getattr(self, '_mock_mode', False) or self.client is None:
            return self._mock_response(operation, args)

        if operation == "search_staff_directory":
            result = await self.client.search_staff(keyword=args.get("keyword"), org_unit_id=args.get("org_unit_id"))
            staff_list = result.get("body", {}).get("result", [])
            if not staff_list:
                return "Không tìm thấy nhân viên phù hợp."
            return "\n".join(
                f"{s['staffName']} ({s['staffCode']}) - {s['title']}, email: {s['email']}" for s in staff_list
            )

        if operation == "list_hr_requests":
            result = await self.client.list_requests(status=args.get("status"), request_type=args.get("request_type"))
            rows = result.get("body", {}).get("result", [])
            if not rows:
                return "Không có đơn từ nào phù hợp."
            return "\n".join(
                f"#{r['id']} {r['requestType']} ({r['status']}) {r['fromDate']}→{r['toDate']}: {r['reason']}"
                for r in rows
            )

        if operation == "get_staff_attendance":
            result = await self.client.get_attendance(
                staff_id=int(args["staff_id"]),
                from_date=args["from_date"],
                to_date=args["to_date"],
            )
            body = result.get("body", {})
            summary = body.get("summary", {})
            return (
                f"Số ngày công: {summary.get('workingDays')}, đi muộn: {summary.get('lateDays')}, "
                f"vắng: {summary.get('absentDays')}."
            )

        if operation == "get_payslip":
            if not args.get("otp"): 
                return "Cần xác thực OTP (step-up verification) trước khi xem bảng lương."
            result = await self.client.get_payslip(month=int(args["month"]), year=int(args["year"]), otp=args["otp"])
            body = result.get("body", {})
            return (
                f"Lương tháng {body.get('month', args['month'])}/{body.get('year', args['year'])}: "
                f"thực nhận {body.get('netIncome'):,} VND (tổng thu nhập {body.get('grossIncome'):,} VND)."
            )

        if operation == "search_company_news":
            result = await self.client.search_news(keyword=args.get("keyword"))
            rows = result.get("body", {}).get("result", [])
            if not rows:
                return "Không có tin tức phù hợp."
            return "\n".join(f"- {n['title']} ({n['categoryName']}): {n['summary']}" for n in rows)

        if operation == "search_notifications":
            result = await self.client.search_notifications(is_read=args.get("is_read"))
            rows = result.get("body", {}).get("result", [])
            if not rows:
                return "Không có thông báo phù hợp."
            return "\n".join(f"- {n['title']}: {n['body']}" for n in rows)

        raise ValueError(f"Unsupported OpenAPI operation: {operation}")

    def _mock_response(self, operation_id: str, args: dict) -> str:
        """Return mock responses for testing/development when MyTascoClient is not available."""
        if operation_id == "search_staff_directory":
            keyword = args.get("keyword", "")
            return f"Nguyễn Văn A (NV001) - Developer, email: nguyenvana@mytasco.com"
        
        if operation_id == "list_hr_requests":
            return "#12345 Leave Request (PENDING) 2024-01-15→2024-01-17: Annual leave"
        
        if operation_id == "get_staff_attendance":
            return "Số ngày công: 20, đi muộn: 2, vắng: 0."
        
        if operation_id == "get_payslip":
            if not args.get("otp"):
                return "Cần xác thực OTP (step-up verification) trước khi xem bảng lương."
            return "Lương tháng 7/2024: thực nhận 15,000,000 VND (tổng thu nhập 18,000,000 VND)."
        
        if operation_id == "search_company_news":
            return "- Q3 Results Released (Corporate): Strong quarterly performance reported"
        
        if operation_id == "search_notifications":
            return "- System Maintenance: Scheduled maintenance on weekend"
        
        return f"[MOCK] Operation {operation_id} with args {args}"

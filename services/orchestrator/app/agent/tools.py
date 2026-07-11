"""
Tool cho LangGraph agent.

RBAC vẫn được enforce ngay trong search_knowledge_base trước khi bất kỳ nội dung
nào vào ngữ cảnh LLM. Các tool nghiệp vụ khác được gọi qua OpenAPI-style gateway
để phù hợp hơn với kiến trúc enterprise tool gateway.
"""
from __future__ import annotations

from langchain_core.tools import tool

from app.core.rbac import can_access
from app.data.loader import get_store
from app.agent.knowledge_base import get_retriever
from app.agent.openapi_gateway import OpenAPIToolGateway, OpenAPIRequest


def build_tools_for_user(user: dict) -> list:
    store = get_store()
    retriever = get_retriever()
    gateway = OpenAPIToolGateway()

    @tool
    def search_knowledge_base(query: str) -> str:
        """Tìm kiếm tài liệu/chính sách/quy trình nội bộ liên quan tới câu hỏi.
        Dùng cho MỌI câu hỏi về chính sách, quy chế, quy trình, tài liệu nội bộ.
        Kết quả trả về đã được lọc theo quyền của người dùng hiện tại — nếu không
        thấy gì nghĩa là không có tài liệu phù hợp NẰM TRONG phạm vi quyền của họ."""
        candidates = retriever.invoke(query)
        allowed: list[str] = []
        for d in candidates:
            full_doc = store.get_document(d.metadata["document_id"])
            if full_doc and can_access(user, full_doc):
                allowed.append(
                    f"[{full_doc['document_id']}] {full_doc['title']} "
                    f"(department: {full_doc['department']}, classification: {full_doc['classification']})\n"
                    f"{full_doc['content_vi']}"
                )
            if len(allowed) >= 4:
                break
        if not allowed:
            return "Không tìm thấy tài liệu phù hợp trong phạm vi quyền truy cập của người dùng hiện tại."
        return "\n\n---\n\n".join(allowed)

    @tool
    async def search_staff_directory(keyword: str) -> str:
        """Tra cứu danh bạ nhân viên My Tasco theo tên, mã nhân viên, hoặc số điện thoại."""
        return await gateway.invoke(OpenAPIRequest(operation_id="search_staff_directory", arguments={"keyword": keyword}))

    @tool
    async def list_hr_requests(status: str | None = None) -> str:
        """Liệt kê đơn từ (nghỉ phép, OT...). status có thể là PENDING, APPROVED, REJECTED, CANCELLED."""
        return await gateway.invoke(OpenAPIRequest(operation_id="list_hr_requests", arguments={"status": status}))

    @tool
    async def get_staff_attendance(staff_id: int, from_date: str, to_date: str) -> str:
        """Xem chấm công của 1 nhân viên trong khoảng ngày (YYYY-MM-DD). Cần staff_id cụ thể."""
        return await gateway.invoke(
            OpenAPIRequest(
                operation_id="get_staff_attendance",
                arguments={"staff_id": staff_id, "from_date": from_date, "to_date": to_date},
            )
        )

    @tool
    async def get_payslip(month: int, year: int, otp: str | None = None) -> str:
        """Xem bảng lương theo tháng/năm. Đây là dữ liệu NHẠY CẢM: nếu chưa có otp,
        phải yêu cầu người dùng cung cấp mã OTP trước, KHÔNG được tự bịa OTP."""
        return await gateway.invoke(OpenAPIRequest(operation_id="get_payslip", arguments={"month": month, "year": year, "otp": otp}))

    @tool
    async def search_company_news(keyword: str | None = None) -> str:
        """Tìm tin tức / thông báo nội bộ theo từ khoá."""
        return await gateway.invoke(OpenAPIRequest(operation_id="search_company_news", arguments={"keyword": keyword}))

    @tool
    async def search_notifications(is_read: bool | None = None) -> str:
        """Tra cứu thông báo nội bộ theo trạng thái đọc/chưa đọc."""
        return await gateway.invoke(OpenAPIRequest(operation_id="search_notifications", arguments={"is_read": is_read}))

    return [
        search_knowledge_base,
        search_staff_directory,
        list_hr_requests,
        get_staff_attendance,
        get_payslip,
        search_company_news,
        search_notifications,
    ]

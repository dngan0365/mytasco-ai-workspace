# Access Control (RBAC/ACL) — cách thực thi

## 1. Ma trận phân quyền (nguồn: sheet `Permissions` / `Roles` trong dataset)

| Classification | Employee | Manager | Director | Executive |
|---|---|---|---|---|
| Public | Allow | Allow | Allow | Allow |
| Internal | Allow | Allow | Allow | Allow |
| Confidential | Allow **chỉ nếu cùng phòng ban** | Allow **chỉ nếu cùng phòng ban** | Allow **chỉ nếu cùng phòng ban** | Allow (mọi phòng ban) |
| Restricted | Deny | Deny | Deny | Allow |

Quy tắc chuẩn hoá phòng ban: `Documents.department` dùng mã ngắn (`"HR"`),
`Users.department` dùng tên đầy đủ (`"Human Resources"`). `app/data/loader.py`
xây bảng alias từ sheet `Departments` (`department_id` / `department_en` /
`department_vi` → cùng 1 mã canonical) để so khớp chính xác 2 định dạng này.

## 2. Nơi logic được cài đặt

`services/orchestrator/app/core/rbac.py::can_access(user, document) -> bool`
là **hàm duy nhất** quyết định quyền truy cập — mọi endpoint đều gọi qua đây,
không có logic phân quyền rải rác nơi khác.

```python
def can_access(user: dict, document: dict) -> bool:
    if document["classification"] in ("Public", "Internal"):
        return True
    if user["role"] == "Executive":
        return True
    if document["classification"] == "Confidential":
        return normalize(user["department"]) == normalize(document["department"])
    return False  # Restricted, không phải Executive
```

## 3. Ba điểm chặn bắt buộc (enforcement points)

| # | Điểm chặn | File | Hành vi khi bị từ chối |
|---|---|---|---|
| 1 | Danh sách tài liệu | `routers/documents.py::list_documents` | Tài liệu không đủ quyền **không xuất hiện** trong danh sách (không phải ẩn/mờ ở frontend, mà bị loại hẳn ở backend) |
| 2 | Chi tiết 1 tài liệu | `routers/documents.py::get_document` | Trả `403 Forbidden`, không trả bất kỳ trường nội dung nào |
| 3 | Truy xuất cho AI Search/Chat | `services/retrieval.py::retrieve` và `agent/tools.py::search_knowledge_base` | Lọc **trước khi** đưa đoạn tài liệu vào ngữ cảnh LLM — mô hình không bao giờ "nhìn thấy" nội dung ngoài phạm vi quyền |

Nguyên tắc cốt lõi: **không tiết lộ sự tồn tại** của tài liệu bị khoá. Khi bị
từ chối, hệ thống trả lời trung lập ("không tìm thấy thông tin phù hợp") thay
vì "tài liệu X tồn tại nhưng bạn không có quyền xem" — tránh rò rỉ thông tin
qua suy luận (ai biết công ty có tài liệu gì đang tồn tại).

## 4. Áp dụng cho cả nhánh agent (LangGraph)

Khi dùng LangGraph ReAct agent (`app/agent/`), việc lọc quyền nằm **bên trong
tool** `search_knowledge_base` (`app/agent/tools.py`), được đóng gói (closure)
theo đúng `user` của request hiện tại:

```python
def build_tools_for_user(user: dict) -> list:
    @tool
    def search_knowledge_base(query: str) -> str:
        candidates = retriever.invoke(query)
        allowed = [d for d in candidates if can_access(user, store.get_document(d.metadata["document_id"]))]
        ...
```

Vì bộ tool được build lại cho từng request (dựa theo user đã xác thực JWT),
LLM (OpenAI model) chỉ có thể nhìn thấy — và do đó chỉ có thể trích dẫn — những tài
liệu đã đi qua bộ lọc `can_access()`. Dù agent có tự do quyết định gọi tool
nào, nó không có cách nào "bypass" ACL vì bộ lọc nằm ở tầng thực thi tool,
không phải ở system prompt (system prompt chỉ là hướng dẫn hành vi, không
phải cơ chế bảo mật).

## 5. Payroll — ví dụ về step-up verification (OTP)

Dữ liệu lương (`get_payslip` tool / endpoint COP `salary-staff-payslip`) là dữ
liệu nhạy cảm bậc cao hơn cả classification thông thường — cần xác thực OTP
trước khi truy xuất, mô phỏng đúng hành vi OTP-gate trong app My Tasco thật:

```python
@tool
async def get_payslip(month: int, year: int, otp: str | None = None) -> str:
    if not otp:
        return "Cần xác thực OTP (step-up verification)... KHÔNG được tự bịa OTP."
    ...
```

System prompt yêu cầu rõ: agent phải hỏi lại người dùng mã OTP, tuyệt đối
không được tự tạo/suy đoán OTP để "hoàn thành" yêu cầu.

## 6. Kiểm thử

- `tests/test_rbac.py` — 7 unit test cho từng tổ hợp classification × vai trò.
- `tests/test_api.py` — test 401 (thiếu token) và 403 (đủ token nhưng sai quyền).
- `GET /evaluation/run` — chấm tự động 50 câu hỏi thật trong dataset, đối
  chiếu permission + retrieval (xem `docs/qa-examples.md` để có số liệu và
  ghi chú minh bạch về 1-2 điểm dữ liệu chưa nhất quán trong chính dataset).


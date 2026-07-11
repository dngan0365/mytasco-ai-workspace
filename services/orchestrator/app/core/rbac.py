"""
Thực thi ma trận phân quyền (sheet Permissions / Roles trong dataset):

  classification   | Employee/Manager/Director        | Executive
  ------------------|-----------------------------------|----------
  Public            | Allow                             | Allow
  Internal          | Allow                              | Allow
  Confidential      | Allow chỉ nếu cùng department      | Allow
  Restricted        | Deny                               | Allow

Nguyên tắc: filter luôn thực hiện Ở TẦNG BACKEND, trước khi đưa nội dung vào
LLM hoặc trả về client — không bao giờ để lộ nội dung/tồn tại của tài liệu
mà người dùng không có quyền xem.
"""
from app.data.loader import Store, get_store

PUBLIC_CLASSIFICATIONS = {"Public", "Internal"}


def _normalize_department(store: Store, department: str | None) -> str | None:
    if not department:
        return None
    return store.department_alias.get(department.strip().lower(), department.strip())


def can_access(user: dict, document: dict) -> bool:
    classification = document["classification"]

    if classification in PUBLIC_CLASSIFICATIONS:
        return True

    if user["role"] == "Executive":
        return True

    if classification == "Confidential":
        store = get_store()
        return _normalize_department(store, user.get("department")) == _normalize_department(
            store, document.get("department")
        )

    # Restricted và không phải Executive
    return False


def filter_accessible(user: dict, documents: list[dict]) -> list[dict]:
    return [doc for doc in documents if can_access(user, doc)]

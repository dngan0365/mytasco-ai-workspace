import os

os.environ.setdefault("DATASET_PATH", "app/data/ai_workspace_dataset_vietnamese_participants.xlsx")

from app.core.rbac import can_access  # noqa: E402
from app.data.loader import get_store  # noqa: E402


def test_public_allowed_for_everyone():
    store = get_store()
    employee = next(u for u in store.users.values() if u["role"] == "Employee")
    public_doc = next(d for d in store.documents.values() if d["classification"] == "Public")
    assert can_access(employee, public_doc)


def test_internal_allowed_for_everyone():
    store = get_store()
    employee = next(u for u in store.users.values() if u["role"] == "Employee")
    internal_doc = next(d for d in store.documents.values() if d["classification"] == "Internal")
    assert can_access(employee, internal_doc)


def test_confidential_denied_cross_department():
    store = get_store()
    hr_employee = next(
        u for u in store.users.values() if u["role"] == "Employee" and u["department"] == "Human Resources"
    )
    finance_confidential = next(
        d
        for d in store.documents.values()
        if d["classification"] == "Confidential" and d["department"] == "Finance"
    )
    assert not can_access(hr_employee, finance_confidential)


def test_confidential_allowed_same_department():
    store = get_store()
    hr_confidential = next(
        d for d in store.documents.values() if d["classification"] == "Confidential" and d["department"] == "HR"
    )
    hr_employee = next(u for u in store.users.values() if u["department"] == "Human Resources")
    assert can_access(hr_employee, hr_confidential)


def test_confidential_allowed_for_executive_any_department():
    store = get_store()
    confidential_doc = next(d for d in store.documents.values() if d["classification"] == "Confidential")
    executive = next(u for u in store.users.values() if u["role"] == "Executive")
    assert can_access(executive, confidential_doc)


def test_restricted_denied_for_non_executive():
    store = get_store()
    restricted_doc = next(d for d in store.documents.values() if d["classification"] == "Restricted")
    non_executive = next(u for u in store.users.values() if u["role"] != "Executive")
    assert not can_access(non_executive, restricted_doc)


def test_restricted_allowed_for_executive():
    store = get_store()
    restricted_doc = next(d for d in store.documents.values() if d["classification"] == "Restricted")
    executive = next(u for u in store.users.values() if u["role"] == "Executive")
    assert can_access(executive, restricted_doc)

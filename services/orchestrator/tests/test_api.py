import os

os.environ.setdefault("DATASET_PATH", "app/data/ai_workspace_dataset_vietnamese_participants.xlsx")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def _login(user_id: str) -> str:
    resp = client.post("/auth/login", json={"user_id": user_id})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_login_unknown_user_returns_404():
    resp = client.post("/auth/login", json={"user_id": "U999"})
    assert resp.status_code == 404


def test_documents_requires_auth():
    resp = client.get("/documents")
    assert resp.status_code == 401


def test_documents_list_filtered_by_acl():
    token = _login("U001")
    resp = client.get("/documents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    docs = resp.json()
    assert all(d["classification"] != "Restricted" for d in docs)


def test_restricted_document_forbidden_for_employee():
    from app.data.loader import get_store

    store = get_store()
    restricted_doc = next(d for d in store.documents.values() if d["classification"] == "Restricted")
    employee = next(u for u in store.users.values() if u["role"] == "Employee")

    token = _login(employee["user_id"])
    resp = client.get(
        f"/documents/{restricted_doc['document_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_evaluation_endpoint_runs():
    resp = client.get("/evaluation/run", params={"limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_questions"] == 5
    assert "permission_accuracy" in body

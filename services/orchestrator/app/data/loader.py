"""
Nạp bộ dataset xlsx (ai_workspace_dataset_vietnamese_participants.xlsx) vào bộ nhớ,
chuẩn hoá dữ liệu, và xây dựng chỉ mục tìm kiếm TF-IDF trên nội dung tiếng Việt.

Toàn bộ dữ liệu được cache 1 lần (lru_cache) — coi như "vector store" đơn giản
cho demo hackathon, không cần Qdrant/DB ngoài vẫn chạy được offline.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import get_settings

# Mỗi sheet có 1 dòng tiêu đề gói (title) + 1 dòng trống trước khi tới header thật
_HEADER_ROW = 2
_SERVICE_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DATASET_PATH = "app/data/ai_workspace_dataset_vietnamese_participants.xlsx"


def _read_sheet(xls: pd.ExcelFile, name: str) -> pd.DataFrame:
    df = pd.read_excel(xls, sheet_name=name, header=_HEADER_ROW)
    return df.dropna(how="all").reset_index(drop=True)


@dataclass
class Store:
    documents: dict[str, dict]
    users: dict[str, dict]
    departments: list[dict]
    department_alias: dict[str, str]
    roles: list[dict]
    permissions: list[dict]
    evaluation: list[dict]
    vectorizer: TfidfVectorizer
    doc_ids: list[str]
    doc_matrix: Any

    def get_user(self, user_id: str) -> dict | None:
        return self.users.get(user_id)

    def get_document(self, document_id: str) -> dict | None:
        return self.documents.get(document_id)

    def list_documents(self) -> list[dict]:
        return list(self.documents.values())

    def search(self, query: str, top_k: int = 5) -> list[tuple[dict, float]]:
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.doc_matrix)[0]
        ranked = sorted(zip(self.doc_ids, scores), key=lambda x: x[1], reverse=True)
        results: list[tuple[dict, float]] = []
        for doc_id, score in ranked[:top_k]:
            if score <= 0:
                continue
            results.append((self.documents[doc_id], float(score)))
        return results


def _build_department_alias(departments: list[dict]) -> dict[str, str]:
    """
    Documents.department dùng department_id ngắn ("HR") trong khi Users.department
    dùng tên đầy đủ ("Human Resources"). Alias map chuẩn hoá cả 2 dạng về department_id.
    """
    alias: dict[str, str] = {}
    for dep in departments:
        canonical = dep["department_id"]
        for key in (dep["department_id"], dep["department_en"], dep["department_vi"]):
            if isinstance(key, str):
                alias[key.strip().lower()] = canonical
    return alias


def _resolve_existing_file(raw_path: str | None, default_path: str, label: str) -> Path:
    path_text = raw_path.strip() if isinstance(raw_path, str) else ""
    path = Path(path_text or default_path)

    candidates = [path] if path.is_absolute() else [_SERVICE_ROOT / path, Path.cwd() / path]
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    first = candidates[0]
    if first.exists() and first.is_dir():
        raise IsADirectoryError(
            f"{label} must point to a file, but resolved to directory: {first}. "
            f"Set {label.upper()} to the Excel file path or leave it unset."
        )

    raise FileNotFoundError(
        f"{label} file not found. Tried: {', '.join(str(c) for c in candidates)}"
    )


@lru_cache
def get_store() -> Store:
    settings = get_settings()

    artifact_path = Path(settings.index_artifact_path.strip() or "../ingestion/output/knowledge_index.pkl")
    if not artifact_path.is_absolute():
        artifact_path = _SERVICE_ROOT / artifact_path
    if artifact_path.exists():
        return _load_from_artifact(artifact_path)

    return _build_from_xlsx(settings)


def _load_from_artifact(artifact_path: Path) -> Store:
    """Nap nhanh index da duoc service ingestion build san (khong can doc lai xlsx)."""
    import pickle

    with artifact_path.open("rb") as f:
        data = pickle.load(f)
    return Store(**data)


def _build_from_xlsx(settings) -> Store:
    path = _resolve_existing_file(settings.dataset_path, _DEFAULT_DATASET_PATH, "dataset_path")
    xls = pd.ExcelFile(path)

    docs_df = _read_sheet(xls, "Documents")
    meta_df = _read_sheet(xls, "Document_Metadata")
    users_df = _read_sheet(xls, "Users")
    dept_df = _read_sheet(xls, "Departments")
    roles_df = _read_sheet(xls, "Roles")
    perm_df = _read_sheet(xls, "Permissions")
    eval_df = _read_sheet(xls, "Public_Evaluation")

    meta_by_id = {row["document_id"]: row.to_dict() for _, row in meta_df.iterrows()}
    documents: dict[str, dict] = {}
    for _, row in docs_df.iterrows():
        doc = row.to_dict()
        meta = meta_by_id.get(doc["document_id"], {})
        doc["owner"] = meta.get("owner")
        doc["allowed_access"] = meta.get("allowed_access")
        doc["tags"] = meta.get("tags")
        doc["last_updated"] = str(meta.get("last_updated"))
        doc["word_count"] = meta.get("word_count")
        documents[doc["document_id"]] = doc

    users = {row["user_id"]: row.to_dict() for _, row in users_df.iterrows()}
    departments = dept_df.to_dict("records")
    department_alias = _build_department_alias(departments)
    roles = roles_df.to_dict("records")
    permissions = perm_df.to_dict("records")
    evaluation = eval_df.to_dict("records")

    doc_ids = list(documents.keys())
    corpus = [documents[d]["content_vi"] for d in doc_ids]
    vectorizer = TfidfVectorizer(max_features=20000, ngram_range=(1, 2))
    doc_matrix = vectorizer.fit_transform(corpus)

    return Store(
        documents=documents,
        users=users,
        departments=departments,
        department_alias=department_alias,
        roles=roles,
        permissions=permissions,
        evaluation=evaluation,
        vectorizer=vectorizer,
        doc_ids=doc_ids,
        doc_matrix=doc_matrix,
    )

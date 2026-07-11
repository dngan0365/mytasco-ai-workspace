"""
Ingestion job — trong hệ thống thật đây là nơi chạy OCR (Textract/Tesseract),
parsing (unstructured.io/python-docx/python-pptx), chunking, và gọi embedding
model (Titan Embed/bge-m3) để nạp tài liệu vào vector store (Qdrant).

Với dataset hackathon, nội dung tiếng Việt (content_vi) đã được trích xuất sẵn
trong sheet Documents, nên bước OCR/parsing được bỏ qua — script này chỉ còn lại
2 việc: (1) gắn metadata phân quyền cho từng tài liệu, (2) build chỉ mục tìm kiếm
(TF-IDF, có thể thay bằng embedding model + Qdrant sau này) và xuất ra 1 artifact
duy nhất (`output/knowledge_index.pkl`) để service orchestrator nạp lại, thay vì
phải đọc/parse lại xlsx mỗi lần khởi động.

Chạy: python build_index.py [--dataset PATH] [--output PATH]
"""
from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

_HEADER_ROW = 2  # mỗi sheet có 1 dòng tiêu đề + 1 dòng trống trước header thật

DEFAULT_DATASET = Path(__file__).parent.parent / "orchestrator" / "app" / "data" / "ai_workspace_dataset_vietnamese_participants.xlsx"
DEFAULT_OUTPUT = Path(__file__).parent / "output" / "knowledge_index.pkl"


def _read_sheet(xls: pd.ExcelFile, name: str) -> pd.DataFrame:
    df = pd.read_excel(xls, sheet_name=name, header=_HEADER_ROW)
    return df.dropna(how="all").reset_index(drop=True)


def _build_department_alias(departments: list[dict]) -> dict[str, str]:
    alias: dict[str, str] = {}
    for dep in departments:
        canonical = dep["department_id"]
        for key in (dep["department_id"], dep["department_en"], dep["department_vi"]):
            if isinstance(key, str):
                alias[key.strip().lower()] = canonical
    return alias


def build_index(dataset_path: Path, output_path: Path) -> None:
    xls = pd.ExcelFile(dataset_path)

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

    artifact = {
        "documents": documents,
        "users": users,
        "departments": departments,
        "department_alias": department_alias,
        "roles": roles,
        "permissions": permissions,
        "evaluation": evaluation,
        "vectorizer": vectorizer,
        "doc_ids": doc_ids,
        "doc_matrix": doc_matrix,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        pickle.dump(artifact, f)

    print(f"[ingestion] Đã index {len(doc_ids)} tài liệu, {len(users)} user -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build_index(args.dataset, args.output)

from fastapi import APIRouter

from app.core.rbac import can_access
from app.data.loader import get_store
from app.services.retrieval import retrieve

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/run")
def run_public_evaluation(limit: int | None = None):
    """
    Chạy (một phần hoặc) toàn bộ sheet Public_Evaluation (50 câu) bằng chính
    user/role/department khai báo trong dataset, so sánh:
      - permission thực tế theo RBAC vs expected_permission
      - tài liệu truy xuất được (AI Search) vs expected_document_id

    Dùng kết quả này làm bằng chứng "access control enforcement" +
    "10 câu hỏi mẫu" + "5 permission test case" khi nộp bài.
    """
    store = get_store()
    rows = store.evaluation[:limit] if limit else store.evaluation

    results = []
    correct_permission = 0
    correct_retrieval = 0

    for row in rows:
        user = store.get_user(row["user_id"])
        expected_ids = [x.strip() for x in str(row["expected_document_id"]).split(";") if x.strip()]
        expected_docs = [store.get_document(doc_id) for doc_id in expected_ids]
        expected_docs = [d for d in expected_docs if d]

        actual_permission = (
            "Allow" if (user and expected_docs and any(can_access(user, d) for d in expected_docs)) else "Deny"
        )
        permission_match = actual_permission == row["expected_permission"]
        correct_permission += int(permission_match)

        retrieved = retrieve(user, row["question_vi"], top_k=5) if user else []
        retrieved_ids = [r["document_id"] for r in retrieved]

        if actual_permission == "Allow":
            retrieval_match = any(doc_id in retrieved_ids for doc_id in expected_ids)
        else:
            # Nếu bị từ chối quyền, tài liệu đó không được phép xuất hiện trong kết quả
            retrieval_match = all(doc_id not in retrieved_ids for doc_id in expected_ids)
        correct_retrieval += int(retrieval_match)

        results.append(
            {
                "question_id": row["question_id"],
                "question_vi": row["question_vi"],
                "user_id": row["user_id"],
                "user_role": row["user_role"],
                "user_department": row["user_department"],
                "expected_permission": row["expected_permission"],
                "actual_permission": actual_permission,
                "permission_match": permission_match,
                "expected_document_id": row["expected_document_id"],
                "retrieved_document_ids": retrieved_ids,
                "retrieval_match": retrieval_match,
                "difficulty": row.get("difficulty"),
            }
        )

    total = len(rows)
    return {
        "total_questions": total,
        "permission_accuracy": round(correct_permission / total, 4) if total else None,
        "retrieval_accuracy": round(correct_retrieval / total, 4) if total else None,
        "details": results,
    }

from __future__ import annotations

import re
from enum import Enum


class IntentRoute(str, Enum):
    rag = "rag"
    tool = "tool"
    human_approval = "human_approval"


_RAG_HINTS = (
    "chính sách",
    "quy chế",
    "quy trình",
    "tài liệu",
    "policy",
    "procedure",
    "document",
)

_TOOL_HINTS = (
    "nhân viên",
    "staff",
    "chấm công",
    "attendance",
    "đơn từ",
    "request",
    "lương",
    "payslip",
    "tin tức",
    "news",
    "thông báo",
    "notification",
)

_HUMAN_APPROVAL_HINTS = (
    "duyệt",
    "phê duyệt",
    "approve",
    "reject",
    "từ chối",
    "create request",
    "tạo đơn",
    "cấp quyền",
    "grant access",
)


def normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", question.lower()).strip()


def route_intent(question: str) -> IntentRoute:
    normalized = normalize_question(question)
    if any(hint in normalized for hint in _HUMAN_APPROVAL_HINTS):
        return IntentRoute.human_approval
    if any(hint in normalized for hint in _TOOL_HINTS):
        return IntentRoute.tool
    if any(hint in normalized for hint in _RAG_HINTS):
        return IntentRoute.rag
    return IntentRoute.rag


def has_real_openai_key(api_key: str | None) -> bool:
    if not api_key:
        return False
    lowered = api_key.lower()
    return "dummy" not in lowered and not lowered.startswith("sk-test")

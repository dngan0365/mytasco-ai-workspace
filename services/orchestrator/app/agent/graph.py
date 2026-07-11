"""
Agent orchestration bằng LangGraph.

Luồng hiện tại bám sát kiến trúc:
- intent router tách RAG / tool / human approval
- RAG agent trả lời từ tài liệu đã lọc ACL
- tool agent gọi enterprise tools qua OpenAPI-style gateway
- guardrail kiểm tra đầu ra trước khi trả về client
"""
from __future__ import annotations

import re

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.agent.tools import build_tools_for_user
from app.agent.router import IntentRoute, has_real_openai_key, route_intent
from app.core.config import get_settings

SYSTEM_PROMPT = (
    "Bạn là trợ lý AI Workspace nội bộ của My Tasco. Luôn ưu tiên gọi tool để lấy "
    "thông tin thay vì tự suy đoán hay bịa đặt. Với câu hỏi về chính sách/quy trình/"
    "tài liệu, dùng search_knowledge_base. Với câu hỏi về nhân sự, chấm công, đơn từ, "
    "lương, tin tức, dùng đúng tool nghiệp vụ tương ứng. Khi trả lời dựa trên tài liệu, "
    "luôn nêu rõ document_id nguồn (dạng [DOC00x]). Nếu tool báo không tìm thấy thông "
    "tin phù hợp (kể cả do không đủ quyền truy cập), hãy nói rõ với người dùng là không "
    "tìm thấy — không được suy diễn hoặc trả lời thay bằng kiến thức nền của bạn."
)

_DOC_ID_PATTERN = re.compile(r"\[(DOC\d+)\]")


def build_agent(user: dict):
    settings = get_settings()
    model = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )
    tools = build_tools_for_user(user)
    return create_react_agent(model, tools, prompt=SYSTEM_PROMPT)


def get_intent_route(question: str) -> IntentRoute:
    return route_intent(question)


def should_use_langgraph_agent() -> bool:
    settings = get_settings()
    return has_real_openai_key(settings.openai_api_key)


def extract_cited_document_ids(messages: list) -> list[str]:
    """Quét toàn bộ tool output (ToolMessage) trong transcript để lấy ra danh sách
    document_id thực sự đã được đưa vào ngữ cảnh (dùng để trả `sources` có cấu trúc
    cho client, ngoài câu trả lời dạng text của agent)."""
    ids: set[str] = set()
    for m in messages:
        if getattr(m, "type", None) == "tool":
            ids.update(_DOC_ID_PATTERN.findall(str(m.content)))
    return sorted(ids)


def guardrail_output(text: str) -> str:
    blocked_patterns = (
        r"(?i)\bssn\b",
        r"(?i)\bcredit card\b",
        r"(?i)\bpassword\b",
    )
    for pattern in blocked_patterns:
        if re.search(pattern, text):
            return "Đầu ra bị chặn bởi guardrail vì chứa thông tin nhạy cảm."
    return text

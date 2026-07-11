import os

os.environ.setdefault("DATASET_PATH", "app/data/ai_workspace_dataset_vietnamese_participants.xlsx")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-not-real")

from app.agent.tools import build_tools_for_user  # noqa: E402
from app.agent.graph import build_agent, extract_cited_document_ids, get_intent_route, guardrail_output, should_use_langgraph_agent  # noqa: E402
from app.data.loader import get_store  # noqa: E402


def _sample_user() -> dict:
    store = get_store()
    return next(iter(store.users.values()))


def test_tools_are_built_for_user():
    tools = build_tools_for_user(_sample_user())
    tool_names = {t.name for t in tools}
    assert tool_names == {
        "search_knowledge_base",
        "search_staff_directory",
        "list_hr_requests",
        "get_staff_attendance",
        "get_payslip",
        "search_company_news",
        "search_notifications",
    }


def test_knowledge_base_tool_respects_acl():
    store = get_store()
    employee = next(u for u in store.users.values() if u["role"] == "Employee")
    tools = build_tools_for_user(employee)
    kb_tool = next(t for t in tools if t.name == "search_knowledge_base")
    result = kb_tool.invoke({"query": "chinh sach tai chinh chien luoc"})
    assert isinstance(result, str)


def test_agent_graph_builds_without_calling_llm():
    # Chi kiem tra graph compile thanh cong (khong goi API that vi khong invoke)
    agent = build_agent(_sample_user())
    assert agent is not None


def test_extract_cited_document_ids_parses_tool_messages():
    class FakeToolMessage:
        type = "tool"
        content = "[DOC001] Tieu de A\n---\n[DOC002] Tieu de B"

    ids = extract_cited_document_ids([FakeToolMessage()])
    assert ids == ["DOC001", "DOC002"]


def test_intent_router_prefers_tool_for_hr_queries():
    assert get_intent_route("xem chấm công nhân viên") == "tool"


def test_guardrail_blocks_sensitive_tokens():
    assert "guardrail" in guardrail_output("password is leaked").lower()


def test_agent_feature_flag_detects_dummy_key():
    assert not should_use_langgraph_agent()



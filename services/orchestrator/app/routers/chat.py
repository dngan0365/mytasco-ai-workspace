from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.agent.graph import build_agent, extract_cited_document_ids, get_intent_route, guardrail_output, should_use_langgraph_agent
from app.core.security import get_current_user
from app.data.loader import get_store
from app.services.retrieval import retrieve

router = APIRouter(prefix="/chat", tags=["ai-chat"])


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
async def ask(payload: AskRequest, user: dict = Depends(get_current_user)):
    intent_route = get_intent_route(payload.question)

    # Chua co key that -> fallback extractive, nhung van di qua intent router
    # de giu cung semantics voi luong production.
    if not should_use_langgraph_agent():
        chunks = retrieve(user, payload.question, top_k=4)
        if not chunks:
            return {
                "answer": "Khong tim thay thong tin phu hop trong pham vi tai lieu ban duoc phep truy cap.",
                "sources": [],
                "mode": "no_context",
                "intent": intent_route.value,
            }
        top = chunks[0]
        snippet = top["content_vi"].split("\n\n")[0][:400]
        return {
            "answer": (
                "(Che do trich xuat - chua cau hinh OPENAI_API_KEY, chua dung duoc LangGraph agent)\n"
                f"Tai lieu lien quan nhat: {top['title']} [{top['document_id']}]\n{snippet}"
            ),
            "sources": [
                {"document_id": c["document_id"], "title": c["title"], "classification": c["classification"]}
                for c in chunks
            ],
            "mode": "extractive_fallback",
            "intent": intent_route.value,
        }

    if intent_route.value == "human_approval":
        return {
            "answer": "Yeu cau nay can buoc phe duyet cua nguoi phu trach. Vui long tao request hoac gui sang human approval node.",
            "sources": [],
            "mode": "human_approval",
            "intent": intent_route.value,
        }

    agent = build_agent(user)
    result = await agent.ainvoke({"messages": [HumanMessage(content=payload.question)]})
    messages = result["messages"]
    final_answer = guardrail_output(messages[-1].content)

    store = get_store()
    cited_ids = extract_cited_document_ids(messages)
    sources = []
    for doc_id in cited_ids:
        doc = store.get_document(doc_id)
        if doc:
            sources.append({"document_id": doc_id, "title": doc["title"], "classification": doc["classification"]})

    return {"answer": final_answer, "sources": sources, "mode": "langgraph-agent", "intent": intent_route.value}




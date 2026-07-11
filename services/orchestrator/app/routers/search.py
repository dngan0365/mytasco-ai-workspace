from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.services.retrieval import retrieve

router = APIRouter(prefix="/search", tags=["ai-search"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("")
def search(payload: SearchRequest, user: dict = Depends(get_current_user)):
    results = retrieve(user, payload.query, top_k=payload.top_k)
    return [{k: v for k, v in r.items() if k != "content_vi"} for r in results]

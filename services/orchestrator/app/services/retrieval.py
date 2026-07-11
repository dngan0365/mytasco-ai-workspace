from app.ai.embeddings.service import get_embedding_service
from app.core.rbac import can_access
from app.data.loader import get_store
from app.repositories.vector_repository import get_vector_repository


def retrieve(user: dict, query: str, top_k: int = 5) -> list[dict]:
    """Semantic search with mandatory ACL pushed into Qdrant."""
    embeddings = get_embedding_service()
    query_vector = embeddings.embed_query(query)
    try:
        return get_vector_repository().search(query_vector, user, top_k)
    except Exception:
        # Offline/test resilience; production readiness requires Qdrant.
        store = get_store()
        docs = store.list_documents()
        vectors = embeddings.embed_documents([doc["content_vi"] for doc in docs])
        ranked = sorted(
            zip(docs, (sum(a * b for a, b in zip(query_vector, vector)) for vector in vectors)),
            key=lambda item: item[1], reverse=True,
        )[: top_k * 3]

    accessible: list[dict] = []
    for doc, score in ranked:
        if can_access(user, doc):
            accessible.append({**doc, "score": score})
        if len(accessible) >= top_k:
            break
    return accessible

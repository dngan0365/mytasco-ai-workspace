from functools import lru_cache

from app.authorization.permission_filter import qdrant_acl_filter
from app.core.config import get_settings


class VectorRepository:
    def __init__(self):
        from qdrant_client import QdrantClient
        self.settings = get_settings()
        self.client = QdrantClient(url=self.settings.qdrant_url, timeout=10)

    def ensure_collection(self):
        from qdrant_client.models import Distance, VectorParams
        if self.settings.qdrant_collection not in {x.name for x in self.client.get_collections().collections}:
            self.client.create_collection(self.settings.qdrant_collection, vectors_config=VectorParams(size=self.settings.embedding_dimension, distance=Distance.COSINE))

    def search(self, vector, user, limit):
        self.ensure_collection()
        hits = self.client.query_points(collection_name=self.settings.qdrant_collection, query=vector, query_filter=qdrant_acl_filter(user), limit=limit, with_payload=True).points
        return [{**(hit.payload or {}), "score": float(hit.score)} for hit in hits]


@lru_cache
def get_vector_repository():
    return VectorRepository()

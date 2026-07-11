import hashlib
import math
from functools import lru_cache

from app.ai.embeddings.base import EmbeddingProvider
from app.core.config import get_settings


class MultilingualEmbeddingService(EmbeddingProvider):
    """Multilingual E5 provider with a deterministic offline test fallback."""

    def __init__(self):
        self.settings = get_settings()
        self.model = None
        if self.settings.embedding_provider == "sentence_transformers":
            try:
                from sentence_transformers import SentenceTransformer
                # Startup and unit tests must never download a model implicitly.
                # Bake the model into the image/cache for production.
                self.model = SentenceTransformer(self.settings.embedding_model, local_files_only=True)
            except (ImportError, OSError):
                pass

    def _fallback(self, text: str) -> list[float]:
        vector = [0.0] * self.settings.embedding_dimension
        for token in " ".join(text.casefold().split()).split():
            digest = hashlib.sha256(token.encode()).digest()
            vector[int.from_bytes(digest[:4], "big") % len(vector)] += 1 if digest[4] & 1 else -1
        norm = math.sqrt(sum(x * x for x in vector)) or 1
        return [x / norm for x in vector]

    def embed_documents(self, texts):
        if self.model is None:
            return [self._fallback(text) for text in texts]
        return [x.tolist() for x in self.model.encode([f"passage: {t}" for t in texts], normalize_embeddings=True)]

    def embed_query(self, text):
        if self.model is None:
            return self._fallback(text)
        return self.model.encode(f"query: {text}", normalize_embeddings=True).tolist()


@lru_cache
def get_embedding_service():
    return MultilingualEmbeddingService()

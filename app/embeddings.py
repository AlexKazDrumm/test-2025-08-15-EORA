from __future__ import annotations
from dataclasses import dataclass
from typing import List, Sequence, Optional

from .config import settings

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


@dataclass
class EmbeddingsBackend:
    name: str
    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:
        raise NotImplementedError
    def embed_one(self, text: str) -> List[float]:
        return self.embed_many([text])[0]


class OpenAIEmbeddings(EmbeddingsBackend):
    def __init__(self):
        if OpenAI is None:
            raise RuntimeError("OpenAI SDK недоступен")
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY не задан")
        self.client = OpenAI(api_key=settings.openai_api_key)
        super().__init__(name="openai")

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:
        model = settings.openai_embedding_model
        try:
            resp = self.client.embeddings.create(input=list(texts), model=model)
            return [d.embedding for d in resp.data]
        except Exception as e:
            if "model_not_found" in str(e) or "does not have access" in str(e):
                fallback = "text-embedding-3-small"
                resp = self.client.embeddings.create(input=list(texts), model=fallback)
                return [d.embedding for d in resp.data]
            raise


class LocalEmbeddings(EmbeddingsBackend):
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(settings.local_embedding_model)
        super().__init__(name="local")

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:
        embs = self.model.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True)
        return [e.tolist() for e in embs]


_backend: Optional[EmbeddingsBackend] = None


def reset_embedder(backend_name: Optional[str] = None) -> None:
    global _backend
    _backend = None
    if backend_name:
        settings.embedding_backend = backend_name  # type: ignore[attr-defined]


def get_embedder() -> EmbeddingsBackend:
    global _backend
    if _backend is not None:
        return _backend
    if settings.embedding_backend == "openai":
        _backend = OpenAIEmbeddings()
    else:
        _backend = LocalEmbeddings()
    return _backend

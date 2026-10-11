"""Embedding client for any OpenAI-compatible /embeddings endpoint (Ollama locally, OpenAI in the cloud)."""
import hashlib
import httpx
import numpy as np
from .config import settings

_cache = {}


def enabled():
    return bool(settings.embedding_base_url and settings.embedding_model)


def _key(text):
    return hashlib.sha256(f"{settings.embedding_model}\0{text}".encode()).hexdigest()


def embed(texts):
    """Return one vector per text. Raises on endpoint failure so callers can fall back."""
    missing = list(dict.fromkeys(text for text in texts if _key(text) not in _cache))
    if missing:
        headers = {"Authorization": f"Bearer {settings.embedding_api_key}"} if settings.embedding_api_key else {}
        response = httpx.post(f"{settings.embedding_base_url.rstrip('/')}/embeddings", headers=headers, timeout=60,
                              json={"model": settings.embedding_model, "input": missing})
        response.raise_for_status()
        data = sorted(response.json()["data"], key=lambda item: item["index"])
        if len(data) != len(missing):
            raise ValueError("Embedding endpoint returned an unexpected number of vectors.")
        for text, item in zip(missing, data):
            _cache[_key(text)] = np.asarray(item["embedding"], dtype=float)
    return [_cache[_key(text)] for text in texts]


def cosine(a, b):
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denominator) if denominator else 0.0

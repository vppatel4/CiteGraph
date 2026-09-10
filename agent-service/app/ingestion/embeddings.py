"""Local sentence embeddings via sentence-transformers.

The model is loaded once and reused. Vectors are L2-normalized so a plain dot
product equals cosine similarity — handy for the citation checks. This module is
the only place that imports the heavy ML library, and it does so lazily so the
lighter code (chunking, metrics, feature extraction) can be imported and tested
without pulling in torch.
"""
from __future__ import annotations

import threading

import numpy as np

from app.config import settings

_model = None
_lock = threading.Lock()


def get_embedder():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_embedder()
    vecs = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.asarray(vecs, dtype=np.float32)


def embed_one(text: str) -> np.ndarray:
    return embed_texts([text])[0]


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity. Works whether or not the inputs are pre-normalized."""
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))

"""Process-wide readiness flags plus a one-time warmup.

The embedding model and the Ollama model both take a few seconds (or, on first
ever run, a few minutes) to become usable. We warm them up in the background at
startup and expose simple booleans so the health endpoint can report progress
instead of blocking. Everything is wrapped in try/except so the HTTP health
endpoint stays up even while the heavy pieces are still loading.
"""
from __future__ import annotations

import logging
import threading

log = logging.getLogger("citegraph.state")

embeddings_ready: bool = False
llm_ready: bool = False
warmup_started: bool = False
_lock = threading.Lock()


def warmup() -> None:
    """Load the embedding model and make sure the Ollama model is pulled."""
    global embeddings_ready, llm_ready, warmup_started
    with _lock:
        if warmup_started:
            return
        warmup_started = True

    def _run() -> None:
        global embeddings_ready, llm_ready
        try:
            from app.ingestion.embeddings import get_embedder

            get_embedder()  # forces the model to load into memory
            embeddings_ready = True
            log.info("embedding model loaded")
        except Exception as exc:  # noqa: BLE001 - stay up regardless
            log.warning("embeddings not ready yet: %s", exc)
        try:
            from app.graph.llm import ensure_model

            ensure_model()  # pulls the model into Ollama if missing
            llm_ready = True
            log.info("ollama model ready")
        except Exception as exc:  # noqa: BLE001
            log.warning("llm not ready yet: %s", exc)

    threading.Thread(target=_run, name="warmup", daemon=True).start()


def detail() -> str:
    return (
        f"embeddings: {'ready' if embeddings_ready else 'loading'}, "
        f"llm: {'ready' if llm_ready else 'loading'}"
    )

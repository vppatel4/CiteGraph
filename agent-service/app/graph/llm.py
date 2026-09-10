"""Talk to the local Ollama model.

Two responsibilities:
  * ensure_model() makes sure the model is pulled (done once at warmup so the
    first user question isn't stuck downloading a couple of GB).
  * get_llm() returns a LangChain ChatOllama the pipeline nodes call.

The LLM is used for exactly two things: splitting a broad question into
sub-questions, and drafting an answer from retrieved text. It is deliberately
*not* trusted to check its own citations — that happens separately.
"""
from __future__ import annotations

import logging

import httpx
from langchain_ollama import ChatOllama

from app.config import settings

log = logging.getLogger("citegraph.llm")

_llm: ChatOllama | None = None


def ensure_model() -> None:
    base = settings.ollama_base_url.rstrip("/")
    # Already present?
    try:
        tags = httpx.get(f"{base}/api/tags", timeout=10).json()
        names = {m.get("name", "") for m in tags.get("models", [])}
        if settings.ollama_model in names or f"{settings.ollama_model}:latest" in names:
            return
    except Exception as exc:  # noqa: BLE001
        log.warning("could not list ollama models: %s", exc)

    log.info("pulling ollama model %s (first run, this can take a while)", settings.ollama_model)
    with httpx.stream(
        "POST",
        f"{base}/api/pull",
        json={"name": settings.ollama_model},
        timeout=None,
    ) as resp:
        for _ in resp.iter_lines():
            pass  # draining the stream blocks until the pull finishes
    log.info("ollama model %s ready", settings.ollama_model)


def get_llm() -> ChatOllama:
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,
        )
    return _llm


def complete(prompt: str) -> str:
    """Run a single prompt and return the text (used by the pipeline nodes)."""
    resp = get_llm().invoke(prompt)
    return (resp.content or "").strip()

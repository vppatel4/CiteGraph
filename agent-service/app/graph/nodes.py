"""The five pipeline steps: decompose, retrieve, draft, verify, finalize.

Each is a plain function that reads and updates a shared state dict. LangGraph
just wires them together (see pipeline.py). Keeping them as ordinary functions
means each step can be reasoned about — and tested — on its own.
"""
from __future__ import annotations

import json
import logging

from app.config import settings
from app.graph import llm
from app.graph.citations import Verifier, verify_answer
from app.graph.prompts import DECOMPOSE_PROMPT, DRAFT_PROMPT, REFUSAL_SENTENCE
from app.ingestion import store

log = logging.getLogger("citegraph.nodes")

MAX_SUBQUESTIONS = 3


# --------------------------------------------------------------------------- #
# decompose
# --------------------------------------------------------------------------- #
def decompose(state: dict) -> dict:
    question = state["question"]
    try:
        raw = llm.complete(DECOMPOSE_PROMPT.format(question=question, max_subs=MAX_SUBQUESTIONS))
        subs = [line.strip("-* \t") for line in raw.splitlines() if line.strip()]
        subs = [s for s in subs if len(s) > 3][:MAX_SUBQUESTIONS]
    except Exception as exc:  # noqa: BLE001 - never let decomposition break the run
        log.warning("decompose failed, using the question as-is: %s", exc)
        subs = []
    if not subs:
        subs = [question]
    state["sub_questions"] = subs
    return state


# --------------------------------------------------------------------------- #
# retrieve
# --------------------------------------------------------------------------- #
def retrieve(state: dict) -> dict:
    from app.ingestion.embeddings import embed_texts

    subs = state["sub_questions"]
    vecs = embed_texts(subs)
    merged: dict[str, object] = {}
    best_similarity = 0.0
    for vec in vecs:
        hits = store.search_chunks(
            state["user_id"], vec, settings.retrieval_top_k, state.get("paper_ids") or None
        )
        for h in hits:
            best_similarity = max(best_similarity, h.similarity)
            # keep the highest-similarity instance of each chunk
            if h.chunk_id not in merged or h.similarity > merged[h.chunk_id].similarity:  # type: ignore[attr-defined]
                merged[h.chunk_id] = h

    ranked = sorted(merged.values(), key=lambda c: c.similarity, reverse=True)  # type: ignore[attr-defined]
    ranked = ranked[: settings.retrieval_top_k]
    state["retrieved"] = ranked
    state["best_similarity"] = best_similarity

    # If nothing is even loosely relevant, refuse before bothering the LLM.
    if not ranked or best_similarity < settings.retrieval_min_similarity:
        state["answered"] = False
        state["refusal_reason"] = "no sufficiently relevant text found in the uploaded papers"
    return state


def has_relevant(state: dict) -> str:
    """Conditional edge: skip drafting entirely when retrieval found nothing."""
    return "draft" if state.get("answered") is not False else "finalize"


# --------------------------------------------------------------------------- #
# draft
# --------------------------------------------------------------------------- #
def _sources_block(retrieved: list) -> str:
    lines = []
    for i, ch in enumerate(retrieved, start=1):
        header = f"[{i}] ({ch.paper_title} — {ch.section}, p.{ch.page})"
        lines.append(f"{header}: {ch.content}")
    return "\n\n".join(lines)


def draft(state: dict) -> dict:
    retrieved = state["retrieved"]
    prompt = DRAFT_PROMPT.format(
        sources=_sources_block(retrieved),
        question=state["question"],
        refusal=REFUSAL_SENTENCE,
    )
    try:
        state["draft"] = llm.complete(prompt)
    except Exception as exc:  # noqa: BLE001
        log.error("draft failed: %s", exc)
        state["draft"] = REFUSAL_SENTENCE
    return state


# --------------------------------------------------------------------------- #
# verify (the actual checking lives in citations.verify_answer)
# --------------------------------------------------------------------------- #
def verify(state: dict) -> dict:
    result = verify_answer(state["draft"], state["retrieved"], Verifier())
    state.update(result)
    return state


# --------------------------------------------------------------------------- #
# finalize
# --------------------------------------------------------------------------- #
def finalize(state: dict) -> dict:
    if state.get("answered") is False:
        state.setdefault("answer", REFUSAL_SENTENCE)
        state["answer"] = REFUSAL_SENTENCE
        state.setdefault("citations", [])
        state.setdefault("dropped", 0)
        state.setdefault("refusal_reason", "the papers don't address this question")

    try:
        store.save_chat(
            state["user_id"],
            state["question"],
            state["answer"],
            bool(state.get("answered", False)),
            json.dumps(state.get("citations", [])),
        )
    except Exception as exc:  # noqa: BLE001 - history is best-effort
        log.warning("could not save chat history: %s", exc)
    return state

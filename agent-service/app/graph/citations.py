"""Citation parsing and verification — the part that makes CiteGraph more than a
plain RAG wrapper.

The draft answer comes back with inline [n] markers pointing at numbered
sources. Here we:
  1. read each line, pull out its [n] markers, and treat the line as a claim;
  2. independently check whether the cited chunk actually supports that claim
     (this check does NOT ask the LLM — it uses embeddings + a small classifier
     or a similarity threshold);
  3. drop any claim whose citations all fail, and drop citations that fail.

If nothing survives, the answer collapses to an honest "not found".

The pure text helpers at the top import nothing heavy, so they can be unit
tested without loading torch. The Verifier loads embeddings lazily.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import settings
from app.eval import classifier as clf
from app.eval.features import extract_features
from app.graph.prompts import REFUSAL_SENTENCE

_MARKER = re.compile(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]")


def parse_markers(line: str) -> list[int]:
    ids: list[int] = []
    for group in _MARKER.findall(line):
        for part in re.split(r"[,;]", group):
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))
    return ids


def strip_markers(line: str) -> str:
    return _MARKER.sub("", line).strip()


def is_structural(line: str) -> bool:
    """A non-claim line we keep as-is (headings, short bullet labels, blanks)."""
    s = line.strip()
    if s == "":
        return True
    if s.startswith("#"):
        return True
    if s.endswith(":"):
        return True
    # A short bullet/label without much content.
    body = re.sub(r"^[-*•–\d.\)\s]+", "", s)
    return len(body.split()) <= 5


def is_refusal(answer: str) -> bool:
    norm = answer.strip().lower().rstrip(".")
    return norm.startswith(REFUSAL_SENTENCE.lower().rstrip("."))


@dataclass
class VerifiedCitation:
    source_index: int
    claim: str
    confidence: float


class Verifier:
    """Decides whether a chunk supports a claim.

    Uses the trained logistic-regression classifier when its file is present;
    otherwise falls back to a plain embedding-similarity threshold. Both paths
    are compared head-to-head in the offline evaluation.
    """

    def __init__(self) -> None:
        self.model = clf.load(settings.classifier_path)
        self.threshold = settings.citation_support_threshold

    @property
    def method(self) -> str:
        return "classifier" if self.model is not None else "threshold"

    def support_score(self, claim: str, chunk_text: str) -> float:
        from app.ingestion.embeddings import cosine, embed_texts

        vecs = embed_texts([claim, chunk_text])
        sim = cosine(vecs[0], vecs[1])
        if self.model is not None:
            feats = extract_features(claim, chunk_text, sim)
            return clf.predict_proba(self.model, feats)
        return sim

    def is_supported(self, score: float) -> bool:
        cutoff = 0.5 if self.model is not None else self.threshold
        return score >= cutoff


SNIPPET_CHARS = 400


def _collapse_blanks(text: str) -> str:
    out: list[str] = []
    prev_blank = False
    for line in text.splitlines():
        blank = line.strip() == ""
        if blank and prev_blank:
            continue
        out.append(line)
        prev_blank = blank
    return "\n".join(out).strip()


def verify_answer(draft_text: str, retrieved: list, verifier: "Verifier") -> dict:
    """Check the draft line by line and keep only claims whose citations hold up.

    `retrieved` is the numbered source list; [n] in the draft refers to
    retrieved[n-1]. Returns the final answer, the surviving citations, how many
    claims were dropped, and whether anything survived at all.
    """
    if is_refusal(draft_text):
        return {
            "answer": REFUSAL_SENTENCE,
            "answered": False,
            "citations": [],
            "dropped": 0,
            "refusal_reason": "the model found nothing in the papers to support an answer",
        }

    kept: list[str] = []
    citations: list[dict] = []
    seen: set[tuple] = set()
    dropped = 0
    any_verified = False

    for line in draft_text.splitlines():
        ids = parse_markers(line)
        if not ids:
            if is_structural(line):
                kept.append(line)
            else:
                dropped += 1  # a factual-looking sentence with no citation
            continue

        claim = strip_markers(line)
        if len(claim.split()) < 2:
            kept.append(line)
            continue

        supported = []
        for idx in ids:
            if 1 <= idx <= len(retrieved):
                ch = retrieved[idx - 1]
                s = verifier.support_score(claim, ch.content)
                if verifier.is_supported(s):
                    supported.append((s, ch))

        if supported:
            kept.append(line)
            any_verified = True
            for s, ch in supported:
                key = (ch.paper_id, ch.chunk_id, claim)
                if key in seen:
                    continue
                seen.add(key)
                citations.append(
                    {
                        "paper_id": ch.paper_id,
                        "paper_title": ch.paper_title,
                        "section": ch.section,
                        "page": ch.page,
                        "snippet": ch.content[:SNIPPET_CHARS],
                        "claim": claim,
                        "confidence": round(float(s), 3),
                        "verified": True,
                    }
                )
        else:
            dropped += 1

    answer = _collapse_blanks("\n".join(kept))
    if not any_verified or not answer:
        return {
            "answer": REFUSAL_SENTENCE,
            "answered": False,
            "citations": [],
            "dropped": dropped,
            "refusal_reason": "no citation in the draft could be verified against the papers",
        }
    return {
        "answer": answer,
        "answered": True,
        "citations": citations,
        "dropped": dropped,
        "refusal_reason": "",
    }

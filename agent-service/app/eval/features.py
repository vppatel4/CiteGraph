"""Features for deciding whether a chunk supports a claim.

Kept deliberately small and interpretable (five features) so the logistic
regression it feeds is easy to explain in an interview: each weight says how
much that signal pushes toward "supports". The embedding similarity is computed
by the caller and passed in, so this module has no heavy dependencies and is
trivial to unit-test.
"""
from __future__ import annotations

import re

FEATURE_NAMES = ["similarity", "keyword_overlap", "number_overlap", "chunk_len", "claim_len"]

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is",
    "are", "was", "were", "be", "been", "by", "as", "that", "this", "these",
    "those", "it", "its", "at", "from", "we", "our", "their", "they", "which",
    "can", "has", "have", "had", "using", "used", "use", "than", "then", "also",
}

_WORD = re.compile(r"[a-zA-Z][a-zA-Z\-']+")
_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def _content_words(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text) if w.lower() not in _STOPWORDS and len(w) > 2}


def keyword_overlap(claim: str, chunk: str) -> float:
    a = _content_words(claim)
    b = _content_words(chunk)
    if not a:
        return 0.0
    # Recall-style: how much of the claim's vocabulary appears in the chunk.
    return len(a & b) / len(a)


def number_overlap(claim: str, chunk: str) -> float:
    claim_nums = set(_NUMBER.findall(claim))
    if not claim_nums:
        return 1.0  # nothing numeric to contradict
    chunk_nums = set(_NUMBER.findall(chunk))
    return len(claim_nums & chunk_nums) / len(claim_nums)


def extract_features(claim: str, chunk: str, similarity: float) -> list[float]:
    return [
        float(similarity),
        keyword_overlap(claim, chunk),
        number_overlap(claim, chunk),
        min(len(chunk.split()) / 300.0, 1.0),
        min(len(claim.split()) / 60.0, 1.0),
    ]

"""Section-aware chunking.

We never let a chunk straddle two sections — that keeps each chunk's "section"
label honest, which matters because we show it in citations. Within a section we
use a simple sliding window over words with a bit of overlap so a sentence split
across a boundary still shows up whole in at least one chunk. Word count is a
good-enough stand-in for tokens here and keeps the logic trivial to explain.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Segment:
    """A paragraph of extracted text tagged with its page and section.

    Defined here (not in pdf.py) so chunking can be imported and tested without
    pulling in PyMuPDF.
    """

    page: int
    section: str
    text: str


@dataclass
class Chunk:
    paper_title: str
    section: str
    page: int
    chunk_index: int
    content: str


def chunk_segments(
    segments: list[Segment],
    paper_title: str,
    size_words: int,
    overlap_words: int,
) -> list[Chunk]:
    if size_words <= 0:
        raise ValueError("size_words must be positive")
    overlap_words = max(0, min(overlap_words, size_words - 1))
    step = size_words - overlap_words

    # Group consecutive segments by section, preserving order.
    grouped: list[tuple[str, list[Segment]]] = []
    for seg in segments:
        if grouped and grouped[-1][0] == seg.section:
            grouped[-1][1].append(seg)
        else:
            grouped.append((seg.section, [seg]))

    chunks: list[Chunk] = []
    index = 0
    for section, segs in grouped:
        # Flatten to (word, page) so a chunk can report the page of its first word.
        words: list[tuple[str, int]] = []
        for seg in segs:
            for w in seg.text.split():
                words.append((w, seg.page))
        if not words:
            continue

        start = 0
        while start < len(words):
            window = words[start : start + size_words]
            content = " ".join(w for w, _ in window)
            page = window[0][1]
            chunks.append(
                Chunk(
                    paper_title=paper_title,
                    section=section,
                    page=page,
                    chunk_index=index,
                    content=content,
                )
            )
            index += 1
            if start + size_words >= len(words):
                break
            start += step

    return chunks

"""Glue for the upload path: PDF bytes -> stored, embedded chunks.

parse -> section-aware chunk -> embed -> store. Returns a small summary the
gateway hands back to the frontend.
"""
from __future__ import annotations

import logging

from app.config import settings
from app.ingestion import store
from app.ingestion.chunking import chunk_segments
from app.ingestion.embeddings import embed_texts
from app.ingestion.pdf import parse_pdf

log = logging.getLogger("citegraph.ingest")


def ingest_paper(user_id: str, filename: str, content: bytes) -> dict:
    title, num_pages, segments = parse_pdf(content, filename)
    chunks = chunk_segments(
        segments,
        paper_title=title,
        size_words=settings.chunk_size_tokens,
        overlap_words=settings.chunk_overlap_tokens,
    )
    if not chunks:
        raise ValueError("no extractable text found in the PDF")

    embeddings = embed_texts([c.content for c in chunks])

    paper_id = store.insert_paper(user_id, title, filename, num_pages)
    store.insert_chunks(paper_id, chunks, embeddings)
    log.info("ingested %s: %d pages, %d chunks", title, num_pages, len(chunks))

    return {
        "paper_id": paper_id,
        "title": title,
        "num_pages": num_pages,
        "num_chunks": len(chunks),
    }

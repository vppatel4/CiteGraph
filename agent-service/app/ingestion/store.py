"""All reads and writes for papers and chunks.

Keeping the SQL in one file makes it easy to see exactly what touches the
database. The similarity search uses pgvector's cosine distance operator (<=>)
and converts it to a 0..1 similarity so the rest of the code deals in
"higher = more similar".
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.db import get_pool
from app.ingestion.chunking import Chunk


@dataclass
class RetrievedChunk:
    chunk_id: str
    paper_id: str
    paper_title: str
    section: str
    page: int
    content: str
    similarity: float


def insert_paper(user_id: str, title: str, filename: str, num_pages: int) -> str:
    with get_pool().connection() as conn:
        row = conn.execute(
            """INSERT INTO papers (user_id, title, filename, num_pages)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (user_id, title, filename, num_pages),
        ).fetchone()
        return str(row[0])


def insert_chunks(paper_id: str, chunks: list[Chunk], embeddings: np.ndarray) -> None:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            for chunk, emb in zip(chunks, embeddings):
                cur.execute(
                    """INSERT INTO chunks
                         (paper_id, paper_title, section, page, chunk_index, content, embedding)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        paper_id,
                        chunk.paper_title,
                        chunk.section,
                        chunk.page,
                        chunk.chunk_index,
                        chunk.content,
                        np.asarray(emb, dtype=np.float32),
                    ),
                )
        conn.execute(
            "UPDATE papers SET num_chunks = %s WHERE id = %s",
            (len(chunks), paper_id),
        )


def search_chunks(
    user_id: str,
    query_embedding: np.ndarray,
    top_k: int,
    paper_ids: list[str] | None = None,
) -> list[RetrievedChunk]:
    query_embedding = np.asarray(query_embedding, dtype=np.float32)
    params: list = [query_embedding, user_id]
    where = "p.user_id = %s"
    if paper_ids:
        where += " AND c.paper_id = ANY(%s)"
        params.append(list(paper_ids))
    sql = f"""
        SELECT c.id, c.paper_id, c.paper_title, c.section, c.page, c.content,
               1 - (c.embedding <=> %s) AS similarity
        FROM chunks c
        JOIN papers p ON p.id = c.paper_id
        WHERE {where}
        ORDER BY c.embedding <=> %s
        LIMIT %s
    """
    # The distance operator appears twice (SELECT + ORDER BY); pass the vector
    # again in the right position.
    ordered_params = [query_embedding] + params[1:] + [query_embedding, top_k]
    with get_pool().connection() as conn:
        rows = conn.execute(sql, ordered_params).fetchall()
    return [
        RetrievedChunk(
            chunk_id=str(r[0]),
            paper_id=str(r[1]),
            paper_title=r[2],
            section=r[3],
            page=r[4],
            content=r[5],
            similarity=float(r[6]),
        )
        for r in rows
    ]


def list_papers(user_id: str) -> list[dict]:
    with get_pool().connection() as conn:
        rows = conn.execute(
            """SELECT id, title, filename, num_pages, num_chunks, created_at
               FROM papers WHERE user_id = %s ORDER BY created_at DESC""",
            (user_id,),
        ).fetchall()
    return [
        {
            "paper_id": str(r[0]),
            "title": r[1],
            "filename": r[2],
            "num_pages": r[3],
            "num_chunks": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
        }
        for r in rows
    ]


def save_chat(user_id: str, question: str, answer: str, answered: bool, citations_json: str) -> None:
    with get_pool().connection() as conn:
        conn.execute(
            """INSERT INTO chat_history (user_id, question, answer, answered, citations)
               VALUES (%s, %s, %s, %s, %s::jsonb)""",
            (user_id, question, answer, answered, citations_json),
        )

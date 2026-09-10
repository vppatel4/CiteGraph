-- This script runs once, automatically, the first time the Postgres container
-- starts (it is mounted into /docker-entrypoint-initdb.d). It sets up the
-- pgvector extension and the whole schema. No manual migration step needed.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- gen_random_uuid()

-- Users of the app. The Go gateway owns this table (signup / login).
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per uploaded paper.
CREATE TABLE IF NOT EXISTS papers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    filename    TEXT NOT NULL,
    num_pages   INT  NOT NULL DEFAULT 0,
    num_chunks  INT  NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_papers_user ON papers(user_id);

-- One row per text chunk, with its locally-computed embedding.
-- 384 dims = the all-MiniLM-L6-v2 sentence-transformers model.
CREATE TABLE IF NOT EXISTS chunks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id     UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    paper_title  TEXT NOT NULL,
    section      TEXT NOT NULL DEFAULT '',
    page         INT  NOT NULL DEFAULT 0,
    chunk_index  INT  NOT NULL DEFAULT 0,
    content      TEXT NOT NULL,
    embedding    VECTOR(384),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_chunks_paper ON chunks(paper_id);

-- Approximate-nearest-neighbour index for fast cosine similarity search.
-- ivfflat needs at least a few rows before it helps; it is harmless when empty.
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Chat history so a user can see their previous questions and answers.
CREATE TABLE IF NOT EXISTS chat_history (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question   TEXT NOT NULL,
    answer     TEXT NOT NULL,
    answered   BOOLEAN NOT NULL DEFAULT TRUE,
    citations  JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id);

-- The seeded demo account is created by the Go gateway on startup (it needs to
-- hash the password with the same bcrypt code the login path uses), not here,
-- so the credentials always match what the login endpoint expects.

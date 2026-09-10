"""One shared Postgres connection pool for the whole process.

pgvector's psycopg adapter is registered on every connection so we can pass and
read numpy vectors directly, and get back Python lists / floats from the
similarity queries.
"""
from __future__ import annotations

from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector

from app.config import settings

_pool: ConnectionPool | None = None


def _configure(conn) -> None:
    register_vector(conn)


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            settings.database_url,
            min_size=1,
            max_size=8,
            configure=_configure,
            open=True,
            timeout=30,
        )
    return _pool

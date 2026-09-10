"""Tiny FastAPI app that exists only for health checks.

The real work is served over gRPC (see grpc_server.py). This HTTP surface is
what Docker Compose and CI poll to know the container is alive, and it reports
whether the heavy models have finished loading.
"""
from __future__ import annotations

from fastapi import FastAPI

from app import state

app = FastAPI(title="CiteGraph Agent", docs_url=None, redoc_url=None)


@app.get("/health")
def health() -> dict:
    # 200 as soon as the process is up; the flags say what is still warming up.
    return {
        "ok": True,
        "embeddings_ready": state.embeddings_ready,
        "llm_ready": state.llm_ready,
        "detail": state.detail(),
    }

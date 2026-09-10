"""Placeholder so the tests directory exists for the Docker build. Real unit
tests for chunking, citation parsing, and eval metrics are added later."""


def test_imports_config():
    from app.config import settings

    assert settings.embedding_dim == 384

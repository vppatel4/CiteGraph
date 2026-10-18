"""Train the citation classifier from the labeled set and save it.

Called once at startup so the running verifier uses the same logistic-regression
model the evaluation reports on (instead of silently falling back to the plain
similarity threshold). Training on 48 examples is a fraction of a second once the
embedding model is loaded.
"""
from __future__ import annotations

import json
import logging

import numpy as np

from app.config import settings
from app.eval import baseline, classifier
from app.eval.features import extract_features

log = logging.getLogger("citegraph.trainer")


def build_and_save(labeled_path: str | None = None, out_path: str | None = None) -> bool:
    labeled_path = labeled_path or settings.labeled_set_path
    out_path = out_path or settings.classifier_path

    from app.ingestion.embeddings import cosine, embed_texts

    with open(labeled_path, "r", encoding="utf-8") as fh:
        rows = json.load(fh)

    claims = [r["claim"] for r in rows]
    chunks = [r["cited_chunk"] for r in rows]
    y = np.array([baseline.label_to_int(r["label"]) for r in rows])

    cv = embed_texts(claims)
    hv = embed_texts(chunks)
    sims = [cosine(cv[i], hv[i]) for i in range(len(rows))]
    feats = np.array(
        [extract_features(claims[i], chunks[i], sims[i]) for i in range(len(rows))],
        dtype=np.float32,
    )

    model = classifier.train(feats, y)
    classifier.save(model, out_path)
    log.info("trained citation classifier on %d examples -> %s", len(rows), out_path)
    return True

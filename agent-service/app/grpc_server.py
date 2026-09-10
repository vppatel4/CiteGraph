"""gRPC servicer — the real API the Go gateway calls.

Health is cheap. IngestPaper runs the upload pipeline. Ask runs the LangGraph
question-answering pipeline. All the actual logic lives in the ingestion/ and
graph/ packages; this file only translates between protobuf messages and those
functions.
"""
from __future__ import annotations

import logging

import grpc

from app import state
from app.graph import pipeline
from app.ingestion.ingest import ingest_paper
from app.proto import citegraph_pb2 as pb
from app.proto import citegraph_pb2_grpc as pb_grpc

log = logging.getLogger("citegraph.grpc")


class AgentServicer(pb_grpc.AgentServiceServicer):
    def Health(self, request, context):  # noqa: N802
        return pb.HealthReply(
            ok=True,
            detail=state.detail(),
            llm_ready=state.llm_ready,
            embeddings_ready=state.embeddings_ready,
        )

    def IngestPaper(self, request, context):  # noqa: N802
        try:
            result = ingest_paper(request.user_id, request.filename, request.content)
        except ValueError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except Exception as exc:  # noqa: BLE001
            log.exception("ingest failed")
            context.abort(grpc.StatusCode.INTERNAL, f"ingest failed: {exc}")
        return pb.IngestReply(
            paper_id=result["paper_id"],
            title=result["title"],
            num_pages=result["num_pages"],
            num_chunks=result["num_chunks"],
        )

    def Ask(self, request, context):  # noqa: N802
        question = (request.question or "").strip()
        if not question:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "question is empty")
        try:
            result = pipeline.run(request.user_id, question, list(request.paper_ids))
        except Exception as exc:  # noqa: BLE001
            log.exception("ask failed")
            context.abort(grpc.StatusCode.INTERNAL, f"ask failed: {exc}")

        citations = [
            pb.Citation(
                paper_id=c["paper_id"],
                paper_title=c["paper_title"],
                section=c["section"],
                page=c["page"],
                snippet=c["snippet"],
                claim=c["claim"],
                confidence=c["confidence"],
                verified=c["verified"],
            )
            for c in result["citations"]
        ]
        return pb.AskReply(
            answer=result["answer"],
            answered=result["answered"],
            citations=citations,
            sub_questions=result["sub_questions"],
            dropped_citations=result["dropped"],
            refusal_reason=result["refusal_reason"],
        )

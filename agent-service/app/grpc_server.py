"""gRPC servicer.

Scaffold version: only Health is implemented so `docker compose up` comes up
green. IngestPaper and Ask are filled in on the agent-service branch once the
ingestion and LangGraph pipeline exist.
"""
from __future__ import annotations

import grpc

from app import state
from app.proto import citegraph_pb2 as pb
from app.proto import citegraph_pb2_grpc as pb_grpc


class AgentServicer(pb_grpc.AgentServiceServicer):
    def Health(self, request, context):  # noqa: N802 (gRPC naming)
        return pb.HealthReply(
            ok=True,
            detail=state.detail(),
            llm_ready=state.llm_ready,
            embeddings_ready=state.embeddings_ready,
        )

    def IngestPaper(self, request, context):  # noqa: N802
        context.abort(grpc.StatusCode.UNIMPLEMENTED, "ingestion not wired yet")

    def Ask(self, request, context):  # noqa: N802
        context.abort(grpc.StatusCode.UNIMPLEMENTED, "ask not wired yet")

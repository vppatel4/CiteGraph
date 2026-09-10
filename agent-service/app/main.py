"""Entry point for the agent service.

Starts two things in one process:
  * a gRPC server (the real API the Go gateway calls)
  * a tiny HTTP server used only for health checks

and kicks off the background model warmup.
"""
from __future__ import annotations

import logging
from concurrent import futures

import grpc
import uvicorn

from app import state
from app.config import settings
from app.grpc_server import AgentServicer
from app.health import app as health_app
from app.proto import citegraph_pb2_grpc

log = logging.getLogger("citegraph.main")

# PDFs can be a few MB; allow generous message sizes.
_MAX_MSG = 64 * 1024 * 1024


def serve_grpc() -> grpc.Server:
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=8),
        options=[
            ("grpc.max_receive_message_length", _MAX_MSG),
            ("grpc.max_send_message_length", _MAX_MSG),
        ],
    )
    citegraph_pb2_grpc.add_AgentServiceServicer_to_server(AgentServicer(), server)
    server.add_insecure_port(f"[::]:{settings.agent_grpc_port}")
    server.start()
    log.info("gRPC server listening on :%d", settings.agent_grpc_port)
    return server


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    state.warmup()
    server = serve_grpc()
    # uvicorn.run blocks; the gRPC server runs in its own threads alongside it.
    uvicorn.run(
        health_app,
        host="0.0.0.0",
        port=settings.agent_http_port,
        log_level="info",
    )
    server.wait_for_termination()


if __name__ == "__main__":
    main()

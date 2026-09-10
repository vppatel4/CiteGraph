# syntax=docker/dockerfile:1
# Build context is the repo root (see docker-compose.yml) so we can copy the
# shared proto/ definitions and generate the gRPC stubs at build time. That
# means a clean clone needs no protoc installed locally.

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch first — much smaller than the default CUDA build.
RUN pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu

COPY agent-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Generate the protobuf/gRPC Python stubs from the shared contract.
COPY proto/ /app/proto/
COPY agent-service/app /app/app
RUN python -m grpc_tools.protoc -I proto \
        --python_out=app/proto --grpc_python_out=app/proto proto/citegraph.proto \
    && python -c "import pathlib;p=pathlib.Path('app/proto/citegraph_pb2_grpc.py');s=p.read_text();p.write_text(s.replace('import citegraph_pb2 as citegraph__pb2','from . import citegraph_pb2 as citegraph__pb2'))"

# Where the tests live (copied so `pytest` works inside the container too).
COPY agent-service/tests /app/tests
COPY eval /app/eval

ENV PYTHONUNBUFFERED=1
EXPOSE 8000 50051

CMD ["python", "-m", "app.main"]

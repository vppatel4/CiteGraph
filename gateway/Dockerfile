# syntax=docker/dockerfile:1
# Build context is the repo root so we can reach the shared proto/ files and
# generate the Go gRPC stubs at build time (no protoc needed on the host).

FROM golang:1.23-bookworm AS build
WORKDIR /src

RUN apt-get update \
    && apt-get install -y --no-install-recommends protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.35.2 \
    && go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1
ENV PATH="/go/bin:${PATH}"

COPY proto/ ./proto/
COPY gateway/ ./gateway/

WORKDIR /src/gateway
RUN mkdir -p internal/pb \
    && protoc -I ../proto \
        --go_out=. --go_opt=module=github.com/vppatel4/citegraph/gateway \
        --go-grpc_out=. --go-grpc_opt=module=github.com/vppatel4/citegraph/gateway \
        ../proto/citegraph.proto
RUN go mod tidy && CGO_ENABLED=0 go build -o /out/gateway ./cmd/gateway

FROM alpine:3.20
RUN apk add --no-cache wget ca-certificates
COPY --from=build /out/gateway /usr/local/bin/gateway
EXPOSE 8080
ENTRYPOINT ["gateway"]

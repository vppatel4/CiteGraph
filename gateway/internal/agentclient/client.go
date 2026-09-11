// Package agentclient wraps the gRPC connection to the Python agent service so
// handlers don't deal with protobuf plumbing directly.
package agentclient

import (
	"context"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"github.com/vppatel4/citegraph/gateway/internal/pb"
)

type Client struct {
	conn  *grpc.ClientConn
	agent pb.AgentServiceClient
}

func New(addr string) (*Client, error) {
	// grpc.NewClient is lazy; the first RPC establishes the connection.
	conn, err := grpc.NewClient(addr,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(64*1024*1024),
			grpc.MaxCallSendMsgSize(64*1024*1024),
		),
	)
	if err != nil {
		return nil, err
	}
	return &Client{conn: conn, agent: pb.NewAgentServiceClient(conn)}, nil
}

func (c *Client) Close() error { return c.conn.Close() }

func (c *Client) Health(ctx context.Context) (*pb.HealthReply, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	return c.agent.Health(ctx, &pb.HealthRequest{})
}

func (c *Client) Ingest(ctx context.Context, userID, filename string, content []byte) (*pb.IngestReply, error) {
	// Ingestion parses, embeds, and stores — allow generous time.
	ctx, cancel := context.WithTimeout(ctx, 5*time.Minute)
	defer cancel()
	return c.agent.IngestPaper(ctx, &pb.IngestRequest{
		UserId:   userID,
		Filename: filename,
		Content:  content,
	})
}

func (c *Client) Ask(ctx context.Context, userID, question string, paperIDs []string) (*pb.AskReply, error) {
	// The local LLM can be slow on first use; give it room.
	ctx, cancel := context.WithTimeout(ctx, 5*time.Minute)
	defer cancel()
	return c.agent.Ask(ctx, &pb.AskRequest{
		UserId:   userID,
		Question: question,
		PaperIds: paperIDs,
	})
}

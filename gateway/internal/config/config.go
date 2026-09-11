// Package config reads every setting from environment variables in one place,
// with sensible defaults so the service runs without a .env in development.
package config

import (
	"os"
	"strconv"
)

type Config struct {
	Port         string
	DatabaseURL  string
	AgentAddr    string
	JWTSecret    string
	JWTTTLHours  int
	RateUpload   int
	RateAsk      int
	DemoEmail    string
	DemoPassword string
	EvalJSONPath string
}

func Load() Config {
	return Config{
		Port:         getenv("GATEWAY_PORT", "8080"),
		DatabaseURL:  getenv("DATABASE_URL", "postgres://citegraph:citegraph@db:5432/citegraph?sslmode=disable"),
		AgentAddr:    getenv("AGENT_GRPC_ADDR", "agent:50051"),
		JWTSecret:    getenv("JWT_SECRET", "change-me-in-real-use-but-fine-for-local-demo"),
		JWTTTLHours:  getenvInt("JWT_TTL_HOURS", 72),
		RateUpload:   getenvInt("RATE_LIMIT_UPLOAD_PER_MIN", 10),
		RateAsk:      getenvInt("RATE_LIMIT_ASK_PER_MIN", 30),
		DemoEmail:    getenv("DEMO_EMAIL", "demo@citegraph.dev"),
		DemoPassword: getenv("DEMO_PASSWORD", "demo1234"),
		EvalJSONPath: getenv("EVAL_RESULTS_JSON", "/eval/results.json"),
	}
}

func getenv(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

func getenvInt(k string, def int) int {
	if v := os.Getenv(k); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return def
}

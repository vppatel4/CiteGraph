// Command gateway is the HTTP front door of CiteGraph: it handles auth and
// uploads, rate-limits the heavy endpoints, and forwards the AI work to the
// Python agent service over gRPC.
package main

import (
	"context"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	chimw "github.com/go-chi/chi/v5/middleware"

	"github.com/vppatel4/citegraph/gateway/internal/agentclient"
	"github.com/vppatel4/citegraph/gateway/internal/auth"
	"github.com/vppatel4/citegraph/gateway/internal/config"
	"github.com/vppatel4/citegraph/gateway/internal/db"
	"github.com/vppatel4/citegraph/gateway/internal/handlers"
	mw "github.com/vppatel4/citegraph/gateway/internal/middleware"
)

func main() {
	cfg := config.Load()
	ctx := context.Background()

	store, err := db.New(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("database: %v", err)
	}
	defer store.Pool.Close()

	// Seed the demo account so reviewers can log in immediately.
	if hash, err := auth.HashPassword(cfg.DemoPassword); err == nil {
		if err := store.SeedDemo(ctx, strings.ToLower(cfg.DemoEmail), hash); err != nil {
			log.Printf("warning: could not seed demo account: %v", err)
		} else {
			log.Printf("demo account ready: %s", cfg.DemoEmail)
		}
	}

	agent, err := agentclient.New(cfg.AgentAddr)
	if err != nil {
		log.Fatalf("agent client: %v", err)
	}
	defer agent.Close()

	r := chi.NewRouter()
	r.Use(chimw.Logger)
	r.Use(chimw.Recoverer)
	r.Use(mw.CORS)

	r.Get("/healthz", handlers.Health(store, agent))

	r.Route("/api", func(r chi.Router) {
		r.Post("/auth/signup", handlers.Signup(store, cfg))
		r.Post("/auth/login", handlers.Login(store, cfg))
		r.Get("/eval", handlers.Eval(cfg))

		// Everything below requires a valid token.
		r.Group(func(r chi.Router) {
			r.Use(mw.Auth(cfg.JWTSecret))
			r.Get("/me", handlers.Me())
			r.Get("/papers", handlers.ListPapers(store))
			r.With(mw.RateLimit(cfg.RateUpload)).Post("/papers", handlers.UploadPaper(agent))
			r.With(mw.RateLimit(cfg.RateAsk)).Post("/ask", handlers.Ask(agent))
		})
	})

	srv := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           r,
		ReadHeaderTimeout: 10 * time.Second,
	}
	log.Printf("gateway listening on :%s", cfg.Port)
	if err := srv.ListenAndServe(); err != nil {
		log.Fatal(err)
	}
}

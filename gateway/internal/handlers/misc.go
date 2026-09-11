package handlers

import (
	"net/http"
	"os"

	"github.com/vppatel4/citegraph/gateway/internal/config"
	"github.com/vppatel4/citegraph/gateway/internal/middleware"
)

// Me returns the logged-in user's basic info (handy for the frontend header).
func Me() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{
			"id":    middleware.UserID(r),
			"email": middleware.Email(r),
		})
	}
}

// Eval serves the evaluation results JSON produced by the eval script (mounted
// into the container). If it hasn't been generated yet, we say so cleanly so the
// dashboard can show a helpful message instead of erroring.
func Eval(cfg config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		data, err := os.ReadFile(cfg.EvalJSONPath)
		if err != nil {
			writeJSON(w, http.StatusOK, map[string]any{
				"available": false,
				"message":   "Run `make eval` to generate evaluation results.",
			})
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(data)
	}
}

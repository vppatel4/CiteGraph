package handlers

import (
	"net/http"

	"github.com/vppatel4/citegraph/gateway/internal/agentclient"
	"github.com/vppatel4/citegraph/gateway/internal/db"
)

// Health reports the gateway plus the two things it depends on. It always
// returns 200 with ok=true if the gateway itself is up, and includes the
// downstream states so the frontend can show "model still warming up".
func Health(store *db.Store, agent *agentclient.Client) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		resp := map[string]any{"ok": true, "service": "gateway"}

		resp["db"] = store.Ping(r.Context()) == nil

		if h, err := agent.Health(r.Context()); err == nil {
			resp["agent"] = map[string]any{
				"ok":               h.Ok,
				"llm_ready":        h.LlmReady,
				"embeddings_ready": h.EmbeddingsReady,
				"detail":           h.Detail,
			}
		} else {
			resp["agent"] = map[string]any{"ok": false, "error": err.Error()}
		}
		writeJSON(w, http.StatusOK, resp)
	}
}

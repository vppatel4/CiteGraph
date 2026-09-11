package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/vppatel4/citegraph/gateway/internal/agentclient"
	"github.com/vppatel4/citegraph/gateway/internal/middleware"
)

type askRequest struct {
	Question string   `json:"question"`
	PaperIDs []string `json:"paper_ids"`
}

type citationDTO struct {
	PaperID    string  `json:"paper_id"`
	PaperTitle string  `json:"paper_title"`
	Section    string  `json:"section"`
	Page       int32   `json:"page"`
	Snippet    string  `json:"snippet"`
	Claim      string  `json:"claim"`
	Confidence float64 `json:"confidence"`
	Verified   bool    `json:"verified"`
}

type askResponse struct {
	Answer           string        `json:"answer"`
	Answered         bool          `json:"answered"`
	Citations        []citationDTO `json:"citations"`
	SubQuestions     []string      `json:"sub_questions"`
	DroppedCitations int32         `json:"dropped_citations"`
	RefusalReason    string        `json:"refusal_reason"`
}

func Ask(agent *agentclient.Client) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req askRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeError(w, http.StatusBadRequest, "invalid request body")
			return
		}
		if strings.TrimSpace(req.Question) == "" {
			writeError(w, http.StatusBadRequest, "question is required")
			return
		}

		reply, err := agent.Ask(r.Context(), middleware.UserID(r), req.Question, req.PaperIDs)
		if err != nil {
			writeError(w, http.StatusBadGateway, "agent error: "+err.Error())
			return
		}

		citations := make([]citationDTO, 0, len(reply.Citations))
		for _, c := range reply.Citations {
			citations = append(citations, citationDTO{
				PaperID:    c.PaperId,
				PaperTitle: c.PaperTitle,
				Section:    c.Section,
				Page:       c.Page,
				Snippet:    c.Snippet,
				Claim:      c.Claim,
				Confidence: c.Confidence,
				Verified:   c.Verified,
			})
		}
		writeJSON(w, http.StatusOK, askResponse{
			Answer:           reply.Answer,
			Answered:         reply.Answered,
			Citations:        citations,
			SubQuestions:     reply.SubQuestions,
			DroppedCitations: reply.DroppedCitations,
			RefusalReason:    reply.RefusalReason,
		})
	}
}

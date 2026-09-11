package handlers

import (
	"io"
	"net/http"
	"strings"

	"github.com/vppatel4/citegraph/gateway/internal/agentclient"
	"github.com/vppatel4/citegraph/gateway/internal/db"
	"github.com/vppatel4/citegraph/gateway/internal/middleware"
)

const maxUploadBytes = 25 << 20 // 25 MB

func ListPapers(store *db.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		papers, err := store.ListPapers(r.Context(), middleware.UserID(r))
		if err != nil {
			writeError(w, http.StatusInternalServerError, "could not list papers")
			return
		}
		writeJSON(w, http.StatusOK, map[string]any{"papers": papers})
	}
}

func UploadPaper(agent *agentclient.Client) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		r.Body = http.MaxBytesReader(w, r.Body, maxUploadBytes)
		if err := r.ParseMultipartForm(maxUploadBytes); err != nil {
			writeError(w, http.StatusBadRequest, "file too large or malformed upload (max 25 MB)")
			return
		}
		file, header, err := r.FormFile("file")
		if err != nil {
			writeError(w, http.StatusBadRequest, "missing 'file' field")
			return
		}
		defer file.Close()

		if !strings.HasSuffix(strings.ToLower(header.Filename), ".pdf") {
			writeError(w, http.StatusBadRequest, "only PDF files are supported")
			return
		}
		content, err := io.ReadAll(file)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "could not read uploaded file")
			return
		}

		reply, err := agent.Ingest(r.Context(), middleware.UserID(r), header.Filename, content)
		if err != nil {
			writeError(w, http.StatusBadGateway, "ingestion failed: "+err.Error())
			return
		}
		writeJSON(w, http.StatusOK, map[string]any{
			"paper_id":   reply.PaperId,
			"title":      reply.Title,
			"num_pages":  reply.NumPages,
			"num_chunks": reply.NumChunks,
		})
	}
}

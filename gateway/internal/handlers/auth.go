package handlers

import (
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"github.com/jackc/pgx/v5/pgconn"

	"github.com/vppatel4/citegraph/gateway/internal/auth"
	"github.com/vppatel4/citegraph/gateway/internal/config"
	"github.com/vppatel4/citegraph/gateway/internal/db"
)

type credentials struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type authResponse struct {
	Token string `json:"token"`
	User  struct {
		ID    string `json:"id"`
		Email string `json:"email"`
	} `json:"user"`
}

func (c credentials) valid() (string, bool) {
	email := strings.TrimSpace(strings.ToLower(c.Email))
	if !strings.Contains(email, "@") {
		return "", false
	}
	if len(c.Password) < 6 {
		return "", false
	}
	return email, true
}

func tokenResponse(w http.ResponseWriter, cfg config.Config, id, email string) {
	tok, err := auth.NewToken(cfg.JWTSecret, id, email, cfg.JWTTTLHours)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "could not create token")
		return
	}
	var resp authResponse
	resp.Token = tok
	resp.User.ID = id
	resp.User.Email = email
	writeJSON(w, http.StatusOK, resp)
}

func Signup(store *db.Store, cfg config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var creds credentials
		if err := json.NewDecoder(r.Body).Decode(&creds); err != nil {
			writeError(w, http.StatusBadRequest, "invalid request body")
			return
		}
		email, ok := creds.valid()
		if !ok {
			writeError(w, http.StatusBadRequest, "email must be valid and password at least 6 characters")
			return
		}
		hash, err := auth.HashPassword(creds.Password)
		if err != nil {
			writeError(w, http.StatusInternalServerError, "could not hash password")
			return
		}
		user, err := store.CreateUser(r.Context(), email, hash)
		if err != nil {
			// unique_violation -> the email is taken
			var pgErr *pgconn.PgError
			if errors.As(err, &pgErr) && pgErr.Code == "23505" {
				writeError(w, http.StatusConflict, "an account with that email already exists")
				return
			}
			writeError(w, http.StatusInternalServerError, "could not create account")
			return
		}
		tokenResponse(w, cfg, user.ID, user.Email)
	}
}

func Login(store *db.Store, cfg config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var creds credentials
		if err := json.NewDecoder(r.Body).Decode(&creds); err != nil {
			writeError(w, http.StatusBadRequest, "invalid request body")
			return
		}
		email := strings.TrimSpace(strings.ToLower(creds.Email))
		user, err := store.GetUserByEmail(r.Context(), email)
		if err != nil || !auth.CheckPassword(user.PasswordHash, creds.Password) {
			// Same message either way so we don't reveal which emails exist.
			writeError(w, http.StatusUnauthorized, "invalid email or password")
			return
		}
		tokenResponse(w, cfg, user.ID, user.Email)
	}
}

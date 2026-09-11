// Package middleware holds the gateway's HTTP middleware: auth, rate limiting,
// and CORS.
package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/vppatel4/citegraph/gateway/internal/auth"
)

type ctxKey string

const (
	userIDKey ctxKey = "userID"
	emailKey  ctxKey = "email"
)

// Auth rejects requests without a valid Bearer token and stashes the user id
// and email in the request context for handlers to read.
func Auth(secret string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			header := r.Header.Get("Authorization")
			if !strings.HasPrefix(header, "Bearer ") {
				http.Error(w, `{"error":"missing bearer token"}`, http.StatusUnauthorized)
				return
			}
			claims, err := auth.ParseToken(secret, strings.TrimPrefix(header, "Bearer "))
			if err != nil {
				http.Error(w, `{"error":"invalid or expired token"}`, http.StatusUnauthorized)
				return
			}
			ctx := context.WithValue(r.Context(), userIDKey, claims.Subject)
			ctx = context.WithValue(ctx, emailKey, claims.Email)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func UserID(r *http.Request) string {
	if v, ok := r.Context().Value(userIDKey).(string); ok {
		return v
	}
	return ""
}

func Email(r *http.Request) string {
	if v, ok := r.Context().Value(emailKey).(string); ok {
		return v
	}
	return ""
}

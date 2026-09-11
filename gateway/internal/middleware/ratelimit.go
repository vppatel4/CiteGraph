package middleware

import (
	"net/http"
	"sync"
	"time"
)

// A tiny per-user token bucket. Each user gets `perMinute` requests that refill
// steadily over a minute. This is intentionally simple and in-memory — it
// protects the heavy upload/ask endpoints from being hammered, which is all we
// need for a local, single-node app.
type bucket struct {
	tokens   float64
	lastFill time.Time
}

type limiter struct {
	mu        sync.Mutex
	buckets   map[string]*bucket
	perMinute float64
}

func RateLimit(perMinute int) func(http.Handler) http.Handler {
	l := &limiter{buckets: map[string]*bucket{}, perMinute: float64(perMinute)}
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			key := UserID(r)
			if key == "" {
				key = r.RemoteAddr
			}
			if !l.allow(key) {
				w.Header().Set("Retry-After", "60")
				http.Error(w, `{"error":"rate limit exceeded, slow down"}`, http.StatusTooManyRequests)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

func (l *limiter) allow(key string) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	b, ok := l.buckets[key]
	if !ok {
		l.buckets[key] = &bucket{tokens: l.perMinute - 1, lastFill: now}
		return true
	}
	// Refill based on elapsed time.
	elapsed := now.Sub(b.lastFill).Minutes()
	b.tokens = min(l.perMinute, b.tokens+elapsed*l.perMinute)
	b.lastFill = now
	if b.tokens < 1 {
		return false
	}
	b.tokens--
	return true
}

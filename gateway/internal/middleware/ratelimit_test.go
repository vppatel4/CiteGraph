package middleware

import (
	"testing"
	"time"
)

func TestBucketAllowsThenBlocks(t *testing.T) {
	l := &limiter{buckets: map[string]*bucket{}, perMinute: 2}

	if !l.allow("user") {
		t.Fatal("first request should be allowed")
	}
	if !l.allow("user") {
		t.Fatal("second request should be allowed")
	}
	if l.allow("user") {
		t.Fatal("third request should be blocked")
	}
}

func TestBucketRefills(t *testing.T) {
	l := &limiter{buckets: map[string]*bucket{}, perMinute: 60}
	l.allow("user") // consume one; bucket now has 59

	// Simulate 1 second passing -> +1 token (60 per minute).
	b := l.buckets["user"]
	b.lastFill = b.lastFill.Add(-1 * time.Second)

	if !l.allow("user") {
		t.Fatal("should be allowed after refill")
	}
}

func TestBucketsArePerKey(t *testing.T) {
	l := &limiter{buckets: map[string]*bucket{}, perMinute: 1}
	if !l.allow("a") {
		t.Fatal("user a first request allowed")
	}
	if !l.allow("b") {
		t.Fatal("user b should have its own bucket")
	}
	if l.allow("a") {
		t.Fatal("user a should now be blocked")
	}
}

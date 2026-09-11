package auth

import "testing"

func TestPasswordRoundTrip(t *testing.T) {
	hash, err := HashPassword("hunter2secret")
	if err != nil {
		t.Fatalf("hash: %v", err)
	}
	if !CheckPassword(hash, "hunter2secret") {
		t.Error("correct password rejected")
	}
	if CheckPassword(hash, "wrong") {
		t.Error("wrong password accepted")
	}
}

func TestTokenRoundTrip(t *testing.T) {
	tok, err := NewToken("secret", "user-123", "a@b.com", 1)
	if err != nil {
		t.Fatalf("new token: %v", err)
	}
	claims, err := ParseToken("secret", tok)
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if claims.Subject != "user-123" {
		t.Errorf("subject = %q, want user-123", claims.Subject)
	}
	if claims.Email != "a@b.com" {
		t.Errorf("email = %q, want a@b.com", claims.Email)
	}
}

func TestTokenWrongSecretRejected(t *testing.T) {
	tok, _ := NewToken("secret", "u", "e", 1)
	if _, err := ParseToken("different-secret", tok); err == nil {
		t.Error("token verified with the wrong secret")
	}
}

func TestExpiredTokenRejected(t *testing.T) {
	// ttl of -1 hour => already expired.
	tok, _ := NewToken("secret", "u", "e", -1)
	if _, err := ParseToken("secret", tok); err == nil {
		t.Error("expired token was accepted")
	}
}

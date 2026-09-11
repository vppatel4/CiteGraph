// Package db is the gateway's thin data layer. The gateway owns the users table
// (signup / login) and only reads the papers table (the agent service writes it
// during ingestion).
package db

import (
	"context"
	"errors"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type Store struct {
	Pool *pgxpool.Pool
}

type User struct {
	ID           string
	Email        string
	PasswordHash string
}

type Paper struct {
	ID        string `json:"paper_id"`
	Title     string `json:"title"`
	Filename  string `json:"filename"`
	NumPages  int    `json:"num_pages"`
	NumChunks int    `json:"num_chunks"`
	CreatedAt string `json:"created_at"`
}

var ErrNotFound = errors.New("not found")

func New(ctx context.Context, url string) (*Store, error) {
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		return nil, err
	}
	if err := pool.Ping(ctx); err != nil {
		return nil, err
	}
	return &Store{Pool: pool}, nil
}

func (s *Store) Ping(ctx context.Context) error {
	return s.Pool.Ping(ctx)
}

// CreateUser inserts a new user and returns the generated id.
func (s *Store) CreateUser(ctx context.Context, email, passwordHash string) (User, error) {
	var id string
	err := s.Pool.QueryRow(ctx,
		`INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id`,
		email, passwordHash,
	).Scan(&id)
	if err != nil {
		return User{}, err
	}
	return User{ID: id, Email: email, PasswordHash: passwordHash}, nil
}

func (s *Store) GetUserByEmail(ctx context.Context, email string) (User, error) {
	var u User
	err := s.Pool.QueryRow(ctx,
		`SELECT id, email, password_hash FROM users WHERE email = $1`, email,
	).Scan(&u.ID, &u.Email, &u.PasswordHash)
	if errors.Is(err, pgx.ErrNoRows) {
		return User{}, ErrNotFound
	}
	return u, err
}

// SeedDemo creates the fixed demo account if it does not already exist. Called
// once at startup so reviewers can log in immediately.
func (s *Store) SeedDemo(ctx context.Context, email, passwordHash string) error {
	_, err := s.Pool.Exec(ctx,
		`INSERT INTO users (email, password_hash) VALUES ($1, $2)
		 ON CONFLICT (email) DO NOTHING`,
		email, passwordHash,
	)
	return err
}

func (s *Store) ListPapers(ctx context.Context, userID string) ([]Paper, error) {
	rows, err := s.Pool.Query(ctx,
		`SELECT id, title, filename, num_pages, num_chunks, created_at
		 FROM papers WHERE user_id = $1 ORDER BY created_at DESC`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	papers := []Paper{}
	for rows.Next() {
		var p Paper
		var created time.Time
		if err := rows.Scan(&p.ID, &p.Title, &p.Filename, &p.NumPages, &p.NumChunks, &created); err != nil {
			return nil, err
		}
		p.CreatedAt = created.Format(time.RFC3339)
		papers = append(papers, p)
	}
	return papers, rows.Err()
}

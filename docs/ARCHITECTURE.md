# Architecture

This is the "why", in plain language. For the "what", see the diagrams and the
tech-stack table in the [README](../README.md).

## The one-sentence version

A Go service handles the boring-but-important web plumbing (accounts, uploads,
rate limiting), and a Python service handles everything that touches AI (reading
PDFs, embeddings, retrieval, drafting, and — the part that matters most —
checking that each citation is real). They talk over gRPC.

## Why two services instead of one

The simplest thing would be a single Python app that does everything. Two
services is a deliberate trade:

- **Separation of concerns.** Auth, JWTs, request validation, and rate limiting
  are a different job from running an AI pipeline. Keeping them apart means the
  "front door" stays small and easy to reason about, and the AI service never
  has to think about HTTP auth.
- **The right tool per job.** Go is a great fit for a fast, concurrent HTTP
  gateway. Python is the only sensible choice for the LangChain/LangGraph/ML
  side. Splitting lets each half use its natural ecosystem.
- **A real systems-design story.** It mirrors how this is actually built in
  production — a thin gateway in front of a heavier internal service — without
  any cloud dependency.

The honest cost: a bit more moving parts and a network hop. For a single-user
local app that's a fine price for the clarity.

## Why gRPC between them (not plain REST)

The gateway↔agent link is an internal, service-to-service call with a fixed,
typed contract (`proto/citegraph.proto`). gRPC gives that a single source of
truth: both sides generate their code from the same `.proto`, so the request and
response shapes can't drift apart. It also handles the binary PDF payload
cleanly. REST would have worked, but the typed contract and generated stubs are
exactly what you want between two services you control.

(The browser still talks to the gateway over ordinary REST/JSON — gRPC is only
the internal hop.)

## Why LangGraph instead of a simple chain

A plain linear chain (retrieve → prompt → answer) can't easily express "if
retrieval found nothing relevant, skip drafting and refuse". LangGraph models the
pipeline as a small state machine with a real branch after retrieval, which is
what makes the honest-refusal path first-class rather than bolted on. It also
keeps each step (decompose, retrieve, draft, verify, finalize) as an independent,
testable function.

## Why pgvector instead of a dedicated vector database

A separate vector DB (Pinecone, Weaviate) would be another service to run and, in
Pinecone's case, an account and a hosted dependency — both of which break the
"zero cost, zero signup, fully local" constraint. pgvector puts the vectors in
the same Postgres that already holds users and papers, so there's one database to
run, one place to back up, and one query language. At this scale it's plenty
fast, and it keeps the whole thing inside Docker.

## Why local embeddings and a local LLM

Hosted embedding and LLM APIs cost money and require accounts and network access.
The brief is a zero-cost, no-signup, fully local project, so embeddings run with
a small `sentence-transformers` model and drafting runs on Ollama. `llama3.2:3b`
is small enough to run on a normal laptop. The trade is quality — a 3B model
drafts less fluently than GPT-4 — but drafting is the only place the model is
used, and its output is verified afterwards, so a smaller model is an acceptable
and honest choice.

## Why the citation verifier is a separate, measured step

"Cited answers" are easy to fake: an LLM can attach `[2]` to a sentence whether
or not source 2 says it. If you then ask the same LLM "is this citation right?",
you're letting it grade its own homework — a weak check. So verification here is
**independent of the LLM**:

- **Baseline:** embedding similarity between the claim and the cited passage,
  above a threshold = supported.
- **Classifier:** a logistic regression over five interpretable features
  (similarity, keyword overlap, numeric-token overlap, chunk length, claim
  length).

Both are scored against a hand-labeled set so we can state a real number. The
classifier is used at runtime when its trained file is present; otherwise the
system falls back to the threshold. Logistic regression (not something bigger)
is deliberate: five features and a linear model are easy to explain and hard to
overfit on a small labeled set, and the evaluation shows it already beats the
threshold — mostly by not being fooled by passages that are similar but wrong.

## Where the data lives

- **users** — owned by the Go gateway (signup/login).
- **papers** and **chunks** (with embeddings) — written by the Python agent
  during ingestion, read by both.
- **chat_history** — written by the agent at the end of each answer.

All in one Postgres instance. The demo account is seeded by the gateway at
startup (so the password is hashed by the same code the login path uses).

## What happens in the edge cases

- **No papers / nothing relevant:** retrieval's best similarity is below the
  floor, so the pipeline refuses before drafting.
- **A wrong citation slips into the draft:** the verifier scores it, it fails,
  and the claim is dropped. If every claim fails, the answer becomes an honest
  "not found".
- **A slow first answer:** the embedding and Ollama models load in the
  background at startup; the health endpoint reports "warming up" until they're
  ready, and the frontend shows that state.

## <a id="optional-groq"></a>Optional: swapping in Groq for faster drafting

The default drafting model is local Ollama and needs no account. If you want
faster responses and are willing to create a **free** Groq account, Groq exposes
an OpenAI-compatible chat endpoint. Because only the draft step calls the LLM,
swapping it is contained to `agent-service/app/graph/llm.py`: point a client at
`https://api.groq.com/openai/v1` with your key and a Groq model name in place of
`ChatOllama`. This is **optional and not part of the default setup** — the
project is designed to run fully locally with no external services.

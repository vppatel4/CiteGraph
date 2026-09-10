# CiteGraph

Multi-paper research Q&A with self-checked citations. Upload research-paper
PDFs, ask a question across all of them, and get an answer where **every
citation is verified against its source before you see it** — and where the
system says "the provided papers don't address this" instead of guessing.

> Full documentation (setup, architecture diagrams, demo checklist, evaluation
> numbers) is added on the docs branch. This is the scaffold.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- Gateway API: http://localhost:8080
- Demo login: `demo@citegraph.dev` / `demo1234`

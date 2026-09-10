# Convenience shortcuts. None of these are required — you can always just run
# the underlying docker/compose commands directly.

.PHONY: up down build logs smoke test test-agent test-gateway eval clean fmt

up:            ## Build and start the whole stack
	docker compose up --build

down:          ## Stop everything
	docker compose down

build:         ## Build all images without starting
	docker compose build

logs:          ## Tail logs from all services
	docker compose logs -f

smoke:         ## Run the end-to-end smoke test against a running stack
	bash scripts/smoke_test.sh

test:          test-agent test-gateway ## Run every test suite

test-agent:    ## Run the Python agent-service unit tests in a container
	docker compose run --rm --no-deps --entrypoint "" agent pytest -q

test-gateway:  ## Run the Go gateway unit tests in a container
	docker build -f gateway/Dockerfile.test -t citegraph-gateway-test . && \
	docker run --rm citegraph-gateway-test

eval:          ## Run the citation-verification + cannot-answer evaluation
	docker compose run --rm --no-deps --entrypoint "" agent \
		python -m app.eval.run_eval --labeled eval/labeled_set.json \
		--cannot-answer eval/cannot_answer_set.json --out eval/results.md

clean:         ## Remove containers and volumes (wipes the database + models)
	docker compose down -v

#!/usr/bin/env bash
# End-to-end smoke test. Assumes `docker compose up` is already running. It waits
# for the agent's models to finish loading, then logs in with the seeded demo
# account, uploads a tiny PDF, lists papers, and asks a question. Used locally
# and in CI.
set -euo pipefail

GATEWAY="${GATEWAY_URL:-http://localhost:8080}"
DEMO_EMAIL="${DEMO_EMAIL:-demo@citegraph.dev}"
DEMO_PASSWORD="${DEMO_PASSWORD:-demo1234}"
READY_TIMEOUT="${READY_TIMEOUT:-600}"

say() { printf "\n\033[1;36m==> %s\033[0m\n" "$1"; }

say "0/5 wait for the stack to be ready (models can take a while on first run)"
deadline=$(( $(date +%s) + READY_TIMEOUT ))
while true; do
  health=$(curl -fsS "${GATEWAY}/healthz" 2>/dev/null || echo "{}")
  if echo "${health}" | grep -q '"llm_ready":true' && echo "${health}" | grep -q '"embeddings_ready":true'; then
    echo "stack ready"
    break
  fi
  if [ "$(date +%s)" -ge "${deadline}" ]; then
    echo "timed out waiting for readiness; last health: ${health}"
    exit 1
  fi
  sleep 5
done

say "1/5 gateway health"
curl -fsS "${GATEWAY}/healthz" | grep -q '"ok":true'
echo "gateway ok"

say "2/5 log in with the seeded demo account"
TOKEN=$(curl -fsS -X POST "${GATEWAY}/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${DEMO_EMAIL}\",\"password\":\"${DEMO_PASSWORD}\"}" \
  | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')
test -n "${TOKEN}"
echo "got a token"

say "3/5 upload a tiny generated PDF"
TMP_PDF="$(mktemp --suffix=.pdf)"
python3 - "$TMP_PDF" <<'PY'
import sys
text = "CiteGraph reduces false positives by verifying every citation against its source chunk."
stream = b"BT /F1 12 Tf 72 720 Td (" + text.encode() + b") Tj ET"
body = (b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n")
body += b"4 0 obj<</Length %d>>stream\n" % len(stream) + stream + b"\nendstream endobj\n"
body += b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
body += b"trailer<</Root 1 0 R>>\n%%EOF"
open(sys.argv[1], "wb").write(body)
PY
UPLOAD=$(curl -fsS --max-time 300 -X POST "${GATEWAY}/api/papers" \
  -H "Authorization: Bearer ${TOKEN}" -F "file=@${TMP_PDF}")
echo "${UPLOAD}" | grep -q '"paper_id"'
echo "upload ok"

say "4/5 list papers"
curl -fsS "${GATEWAY}/api/papers" -H "Authorization: Bearer ${TOKEN}" | grep -q '"paper_id"'
echo "list ok"

say "5/5 ask a question"
ASK=$(curl -fsS --max-time 300 -X POST "${GATEWAY}/api/ask" \
  -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' \
  -d '{"question":"How does CiteGraph reduce false positives?"}')
echo "${ASK}" | grep -q '"answer"'
echo "ask ok"

rm -f "${TMP_PDF}"
say "SMOKE TEST PASSED"

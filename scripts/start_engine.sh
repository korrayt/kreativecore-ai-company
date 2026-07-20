#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
RUNTIME="$ROOT/.engine-runtime"
SERVER="$(cat "$RUNTIME/server-path.txt")"
MODEL="$(cat "$RUNTIME/model-path.txt")"
PORT="${LLAMA_PORT:-8080}"
export LD_LIBRARY_PATH="$(dirname "$SERVER"):${LD_LIBRARY_PATH:-}"
"$SERVER" -m "$MODEL" -c "${LLAMA_CONTEXT:-4096}" -t "${LLAMA_THREADS:-2}" --host 127.0.0.1 --port "$PORT" > "$RUNTIME/server.log" 2>&1 &
PID=$!
echo "$PID" > "$RUNTIME/server.pid"
for _ in $(seq 1 120); do
  if curl --fail --silent "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    echo 'Local AI engine is ready.'
    exit 0
  fi
  if ! kill -0 "$PID" >/dev/null 2>&1; then
    cat "$RUNTIME/server.log" >&2
    exit 1
  fi
  sleep 2
done
cat "$RUNTIME/server.log" >&2
exit 1

#!/bin/zsh
set -eu

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$DEMO_DIR/.polis_demo_server.pid"
PORT_FILE="$DEMO_DIR/.polis_demo_server.port"
LOG_FILE="$DEMO_DIR/polis_demo_server.log"

if [[ -f "$PID_FILE" && -f "$PORT_FILE" ]] && kill -0 "$(<"$PID_FILE")" 2>/dev/null; then
  PORT="$(<"$PORT_FILE")"
  open "http://127.0.0.1:${PORT}/index.html"
  exit 0
fi

PORT="$(python3 - <<'PY'
import socket

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"

cd "$DEMO_DIR"
nohup python3 -m http.server "$PORT" --bind 127.0.0.1 >"$LOG_FILE" 2>&1 &
SERVER_PID=$!
print -r -- "$SERVER_PID" > "$PID_FILE"
print -r -- "$PORT" > "$PORT_FILE"

sleep 1
open "http://127.0.0.1:${PORT}/index.html"

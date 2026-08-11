#!/bin/zsh
set -eu

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$DEMO_DIR/.polis_demo_server.pid"
PORT_FILE="$DEMO_DIR/.polis_demo_server.port"

if [[ -f "$PID_FILE" ]]; then
  SERVER_PID="$(<"$PID_FILE")"
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID"
  fi
fi

rm -f "$PID_FILE" "$PORT_FILE"

#!/bin/bash
# Start MT5 Router backend with correct Docker socket

export DOCKER_HOST=unix:///var/run/docker.sock
cd "$(dirname "$0")/backend"

echo "Starting MT5 Router backend..."
echo "Docker socket: $DOCKER_HOST"

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 "$@"

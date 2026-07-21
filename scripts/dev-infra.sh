#!/usr/bin/env bash
# Starts Postgres + Redis (see docker-compose.yml) and waits until both
# report healthy. Idempotent — safe to run on every codespace start,
# whether the containers already exist, are stopped, or don't exist yet.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found — skipping infra startup (are you outside a container with Docker available?)"
  exit 0
fi

docker compose up -d postgres redis

echo "Waiting for postgres + redis to report healthy..."
for _ in $(seq 1 30); do
  postgres_status=$(docker compose ps -q postgres | xargs -r docker inspect -f '{{.State.Health.Status}}' 2>/dev/null || echo "starting")
  redis_status=$(docker compose ps -q redis | xargs -r docker inspect -f '{{.State.Health.Status}}' 2>/dev/null || echo "starting")
  if [ "$postgres_status" = "healthy" ] && [ "$redis_status" = "healthy" ]; then
    echo "postgres + redis are healthy."
    exit 0
  fi
  sleep 1
done

echo "Warning: postgres/redis did not report healthy within 30s (postgres=$postgres_status, redis=$redis_status)." >&2
echo "Check 'docker compose logs postgres redis' if the backend fails to connect." >&2

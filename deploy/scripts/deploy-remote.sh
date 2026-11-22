#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

ENV_FILE="${ENV_FILE:-.env}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
REGISTRY="${REGISTRY:-ghcr.io/zzbazzzbaz}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

cd "${DEPLOY_DIR}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed on deploy host." >&2
  exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
  echo "${DEPLOY_DIR}/${ENV_FILE} does not exist. Create it from backend/.env.example before deploying." >&2
  exit 1
fi

if ! grep -q '^DJANGO_SECRET_KEY=' "${ENV_FILE}"; then
  echo "DJANGO_SECRET_KEY is missing in ${DEPLOY_DIR}/${ENV_FILE}." >&2
  exit 1
fi

set_env() {
  key="$1"
  value="$2"

  if grep -q "^${key}=" "${ENV_FILE}"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "${ENV_FILE}"
  else
    printf '%s=%s\n' "${key}" "${value}" >> "${ENV_FILE}"
  fi
}

sudo_auth() {
  if sudo -n true >/dev/null 2>&1; then
    return 0
  fi

  if [ -z "${DEPLOY_PASSWORD:-}" ]; then
    echo "sudo requires DEPLOY_PASSWORD on this host." >&2
    exit 1
  fi

  printf '%s\n' "${DEPLOY_PASSWORD}" | sudo -S true >/dev/null 2>&1
}

docker_run() {
  if docker ps >/dev/null 2>&1; then
    docker "$@"
  else
    sudo_auth
    sudo -n docker "$@"
  fi
}

registry_username="${REGISTRY_USERNAME:-${GITEA_ACTOR:-}}"
if [ -z "${registry_username}" ]; then
  echo "REGISTRY_USERNAME or GITEA_ACTOR is required for registry login." >&2
  exit 1
fi

if [ -z "${REGISTRY_TOKEN:-}" ]; then
  echo "REGISTRY_TOKEN is required for registry login." >&2
  exit 1
fi

set_env IMAGE_TAG "${IMAGE_TAG}"

echo "${REGISTRY_TOKEN}" | docker_run login "${REGISTRY}" -u "${registry_username}" --password-stdin
docker_run compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" config >/dev/null
docker_run compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" pull
docker_run compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --remove-orphans
docker_run compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps

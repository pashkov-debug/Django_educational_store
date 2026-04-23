#!/usr/bin/env bash
set -euo pipefail

: "${DEPLOY_HOST:?DEPLOY_HOST is required}"
: "${DEPLOY_USER:?DEPLOY_USER is required}"
: "${DEPLOY_PATH:?DEPLOY_PATH is required}"
: "${REPO_URL:?REPO_URL is required}"

BRANCH="${BRANCH:-main}"
SSH_OPTS="${SSH_OPTS:-}"

ssh ${SSH_OPTS} "${DEPLOY_USER}@${DEPLOY_HOST}" "mkdir -p '${DEPLOY_PATH}'"

ssh ${SSH_OPTS} "${DEPLOY_USER}@${DEPLOY_HOST}" "
set -e
if [ ! -d '${DEPLOY_PATH}/.git' ]; then
  git clone '${REPO_URL}' '${DEPLOY_PATH}'
fi
cd '${DEPLOY_PATH}'
git fetch --all
git checkout '${BRANCH}'
git pull --ff-only origin '${BRANCH}'
if [ ! -f .env ]; then
  cp .env.example .env
  echo '.env создан из .env.example. Проверь значения перед первым публичным запуском.'
fi
docker compose up -d --build
docker compose ps
"

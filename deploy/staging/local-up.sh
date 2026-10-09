#!/usr/bin/env bash
# =============================================================================
# erp-staging LOCAL FALLBACK - runs the staging stack on a developer machine
# (Docker Desktop) when the VM deploy is not approved. Same docker-compose.yml
# as the VM, but a separate project, env file, images and credentials:
#
#   project      erp-staging-local          (VM: erp-staging)
#   env file     ./.env.local               (VM: ./.env)
#   images       erp-staging/api:<sha>, erp-staging/{frontend,portal}:<sha>-local
#   frontends    baked for http://localhost:18000
#   credentials  ./credentials.local.txt    (VM: ./credentials.txt)
#   URLs         synergy http://localhost:13000, portal http://localhost:13001,
#                API http://localhost:18000
#
# This script only talks to the local Docker daemon. It has no ssh, no
# docker save/load and no remote host; deploy.sh and preflight.sh stay VM-only.
#
#   ./local-up.sh init         create .env.local with freshly generated secrets
#   ./local-up.sh build [ref]  build the three images from a clean checkout of
#                              <ref> (default: HEAD) - uncommitted changes are
#                              never built
#   ./local-up.sh up           guardrails, then start db+api, then the frontends
#   ./local-up.sh seed         evaluation seed (seed-eval.sh --local)
#   ./local-up.sh stop         stop containers (keeps volumes)
#   ./local-up.sh status | logs [svc]
#   ./local-up.sh reset        stop and DELETE the local volumes (local DB only)
# =============================================================================
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(git -C "$DIR" rev-parse --show-toplevel)"
PROJECT="erp-staging-local"
ENV_FILE="$DIR/.env.local"
LOCAL_API_ORIGIN="http://localhost:18000"
# Origins that must never appear in a local bundle: production, the dev default,
# and any private-network address (i.e. an image baked for a LAN deployment).
FORBIDDEN_FIXED=("zchpcerp.zchpc.ac.zw" "employees.zchpc.ac.zw" "localhost:8000")
FORBIDDEN_REGEX='https?://(10|192\.168|172\.(1[6-9]|2[0-9]|3[01]))\.'

die() { echo "LOCAL ABORT: $*" >&2; exit 1; }

COMPOSE=(docker compose -p "$PROJECT" -f "$DIR/docker-compose.yml" --env-file "$ENV_FILE")

gen() { head -c 96 /dev/urandom | base64 | tr -d '/+=\n' | head -c "$1"; }

load_env() {
  [ -f "$ENV_FILE" ] || die "missing $ENV_FILE; run ./local-up.sh init"
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
  [ "${COMPOSE_PROJECT_NAME:-}" = "$PROJECT" ] || die "COMPOSE_PROJECT_NAME in $ENV_FILE must be $PROJECT"
  [ "${ZCHPC_ENV:-}" = "staging" ] || die "ZCHPC_ENV must be staging"
  [ -n "${IMAGE_TAG:-}" ] || die "IMAGE_TAG is empty; run ./local-up.sh build"
  export API_IMAGE="erp-staging/api:${IMAGE_TAG}"
  export FRONTEND_IMAGE="erp-staging/frontend:${IMAGE_TAG}-local"
  export PORTAL_IMAGE="erp-staging/portal:${IMAGE_TAG}-local"
  # Every origin and host in the local env must be loopback.
  local item
  for item in ${STAGING_HOSTS//,/ }; do
    case "$item" in localhost|127.0.0.1) ;; *) die "STAGING_HOSTS may only contain localhost/127.0.0.1 (found '$item')" ;; esac
  done
  for item in ${STAGING_ORIGINS//,/ }; do
    case "$item" in http://localhost:*|http://127.0.0.1:*) ;; *) die "STAGING_ORIGINS may only contain loopback origins (found '$item')" ;; esac
  done
}

set_image_tag() {  # rewrite IMAGE_TAG in .env.local
  local tmp
  tmp="$(mktemp "$DIR/.env.local.XXXXXX")"
  grep -v '^IMAGE_TAG=' "$ENV_FILE" > "$tmp" || true
  echo "IMAGE_TAG=$1" >> "$tmp"
  mv "$tmp" "$ENV_FILE"
}

bundle_guardrail() {  # bundle_guardrail <image>
  local image="$1" bundle o
  bundle="$(docker run --rm --network none --entrypoint sh "$image" \
    -c 'cat /usr/share/nginx/html/assets/*.js')" || die "cannot read bundle of $image"
  for o in "${FORBIDDEN_FIXED[@]}"; do
    if grep -qF "$o" <<<"$bundle"; then die "bundle of $image contains forbidden origin '$o'"; fi
  done
  if grep -qE "$FORBIDDEN_REGEX" <<<"$bundle"; then
    die "bundle of $image contains a private-network origin (LAN build?)"
  fi
  grep -qF "$LOCAL_API_ORIGIN" <<<"$bundle" || die "bundle of $image does not contain $LOCAL_API_ORIGIN"
  echo "  ok  bundle guardrail $image"
}

wait_healthy() {  # wait_healthy <service> <timeout-seconds>
  local svc="$1" t="$2" id state=""
  id="$("${COMPOSE[@]}" ps -q "$svc")"
  [ -n "$id" ] || die "service $svc has no container"
  for _ in $(seq "$t"); do
    state="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}nohc:{{.State.Status}}{{end}}' "$id")"
    case "$state" in
      healthy) echo "  ok  $svc healthy"; return 0 ;;
      nohc:running) echo "  ok  $svc running (no healthcheck defined)"; return 0 ;;
    esac
    sleep 1
  done
  die "$svc not healthy after ${t}s (state: $state); see ./local-up.sh logs $svc"
}

cmd="${1:-}"
case "$cmd" in
  init)
    [ -e "$ENV_FILE" ] && die "$ENV_FILE already exists; delete it first to regenerate secrets"
    umask 077
    cat > "$ENV_FILE" <<EOF
# erp-staging LOCAL fallback - generated by local-up.sh init. Never commit.
COMPOSE_PROJECT_NAME=$PROJECT
ZCHPC_ENV=staging
POSTGRES_DB=erp_staging_local
POSTGRES_USER=erp_staging_local
POSTGRES_PASSWORD=$(gen 32)
SECRET_KEY=$(gen 64)
STAGING_HOSTS=localhost,127.0.0.1
STAGING_ORIGINS=http://localhost:13000,http://localhost:13001,http://127.0.0.1:13000,http://127.0.0.1:13001
DRF_NUM_PROXIES=0
STAGING_API_PORT=18000
STAGING_FRONTEND_PORT=13000
STAGING_PORTAL_PORT=13001
IMAGE_TAG=
EOF
    echo "  ok  wrote $ENV_FILE (fresh secrets, not printed)"
    ;;
  build)
    [ -f "$ENV_FILE" ] || die "missing $ENV_FILE; run ./local-up.sh init"
    ref="${2:-HEAD}"
    sha="$(git -C "$REPO" rev-parse --short "$ref^{commit}")" || die "unknown ref '$ref'"
    src="$(mktemp -d)"
    trap 'git -C "$REPO" worktree remove --force "$src" >/dev/null 2>&1 || true' EXIT
    git -C "$REPO" worktree add --detach "$src" "$sha" >/dev/null
    echo "== building $sha from a clean checkout"
    if docker image inspect "erp-staging/api:$sha" >/dev/null 2>&1; then
      echo "  --  erp-staging/api:$sha already present (origin-independent), reused"
    else
      docker build --target production -t "erp-staging/api:$sha" "$src/erp_project"
    fi
    docker build --build-arg VITE_API_URL="$LOCAL_API_ORIGIN" -t "erp-staging/frontend:$sha-local" "$src/zchpc-erp-synergy-main"
    docker build --build-arg VITE_API_URL="$LOCAL_API_ORIGIN" -t "erp-staging/portal:$sha-local" "$src/employee-portal"
    set_image_tag "$sha"
    echo "== built; IMAGE_TAG=$sha recorded in $ENV_FILE"
    ;;
  up)
    load_env
    echo "== $PROJECT up ($IMAGE_TAG)"
    for ref in "$API_IMAGE" "$FRONTEND_IMAGE" "$PORTAL_IMAGE"; do
      docker image inspect "$ref" >/dev/null 2>&1 || die "image $ref not found; run ./local-up.sh build"
    done
    case "$SECRET_KEY" in ""|*__generate__*) die "SECRET_KEY is not set";; esac
    [ "${#SECRET_KEY}" -ge 50 ] || die "SECRET_KEY must be at least 50 characters"
    bundle_guardrail "$FRONTEND_IMAGE"
    bundle_guardrail "$PORTAL_IMAGE"
    "${COMPOSE[@]}" config -q || die "compose config invalid"
    "${COMPOSE[@]}" up -d --pull never --no-build db api
    wait_healthy db 60
    wait_healthy api 180
    "${COMPOSE[@]}" up -d --pull never --no-build frontend portal
    wait_healthy frontend 60
    wait_healthy portal 60
    echo "== up: synergy http://localhost:13000  portal http://localhost:13001  api $LOCAL_API_ORIGIN"
    ;;
  seed) load_env; "$DIR/seed-eval.sh" --local ;;
  stop) load_env; "${COMPOSE[@]}" stop ;;
  status) load_env; "${COMPOSE[@]}" ps ;;
  logs) load_env; shift; "${COMPOSE[@]}" logs --tail 200 "$@" ;;
  reset) load_env; "${COMPOSE[@]}" down -v ;;
  *) die "usage: local-up.sh init | build [ref] | up | seed | stop | status | logs [svc] | reset" ;;
esac

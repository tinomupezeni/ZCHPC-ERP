#!/usr/bin/env bash
# =============================================================================
# erp-staging deploy wrapper - the ONLY supported way to operate the staging
# stack on the production VM. Lives in /home/user/erp-staging/ next to
# docker-compose.yml, .env (chmod 600), preflight.sh and seed-eval.sh.
#
# Run with sudo:  sudo ./deploy.sh <action>
# Production's .env (/home/user/zchpc-erp/.env) is root-owned and deploy.sh must
# read it to prove staging's secrets differ; the check is never skipped. The
# script uses absolute paths only, so sudo's changed $HOME does not matter.
#
#   ./deploy.sh up       guarded start/update (images must already be loaded)
#   ./deploy.sh stop     stop staging containers (keeps volumes)
#   ./deploy.sh status   show staging containers
#   ./deploy.sh logs [svc]
#
# There is deliberately no `down -v`, no prune, no pull and no build here.
#
# Images are built OFF the VM and transferred (VM builds are last resort and
# need explicit approval). From a clean checkout of `master` on your machine:
#
#   SHA=$(git rev-parse --short HEAD)
#   docker build --target production -t erp-staging/api:$SHA erp_project
#   docker build --build-arg VITE_API_URL=<STAGING_FRONTEND_API_ORIGIN> \
#       -t erp-staging/frontend:$SHA zchpc-erp-synergy-main
#   docker build --build-arg VITE_API_URL=<STAGING_PORTAL_API_ORIGIN> \
#       -t erp-staging/portal:$SHA employee-portal
#   docker save erp-staging/api:$SHA erp-staging/frontend:$SHA erp-staging/portal:$SHA \
#       | gzip | ssh erp-vm 'gunzip | docker load'
#
# WARNING: both frontend Dockerfiles default VITE_API_URL to the PRODUCTION
# origin. Forgetting --build-arg bakes production in; the bundle guardrail
# below refuses such images.
# =============================================================================
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="erp-staging"
PROD_DIR="/home/user/zchpc-erp"
OLD_STAGING_DIR="/home/user/zchpc-erp-staging"
FORBIDDEN_ORIGINS=("zchpcerp.zchpc.ac.zw" "employees.zchpc.ac.zw" "localhost:8000" "10.50.14.12:8000" "10.50.14.12:8001")

die() { echo "DEPLOY ABORT: $*" >&2; exit 1; }

# --- 0. location and env file -------------------------------------------------
[ "$DIR" != "$PROD_DIR" ] && [ "$DIR" != "$OLD_STAGING_DIR" ] \
  || die "deploy.sh must not run from $DIR"
[ -f "$DIR/.env" ] || die "missing $DIR/.env (copy .env.example and generate secrets)"
[ "$(stat -c %a "$DIR/.env")" = "600" ] || die "$DIR/.env must be chmod 600"
[ -f "$DIR/docker-compose.yml" ] || die "missing $DIR/docker-compose.yml"

set -a
# shellcheck disable=SC1091
. "$DIR/.env"
set +a

# --- 1. identity: all three project-name sources must agree --------------------
[ "${COMPOSE_PROJECT_NAME:-}" = "$PROJECT" ] || die "COMPOSE_PROJECT_NAME must be $PROJECT"
[ "${ZCHPC_ENV:-}" = "staging" ] || die "ZCHPC_ENV must be staging"
grep -qx "name: $PROJECT" "$DIR/docker-compose.yml" || die "compose file is not pinned to 'name: $PROJECT'"
grep -q "container_name:" "$DIR/docker-compose.yml" && die "compose file must not set container_name"
grep -qE "^\s+(external|name):" "$DIR/docker-compose.yml" && die "compose file must not name or reference external volumes/networks"

COMPOSE=(docker compose -p "$PROJECT" -f "$DIR/docker-compose.yml" --env-file "$DIR/.env")

# --- helpers -------------------------------------------------------------------
normalize() {  # strip surrounding whitespace, then one layer of matching quotes
  local v="$1"
  v="${v#"${v%%[![:space:]]*}"}"
  v="${v%"${v##*[![:space:]]}"}"
  if [ "${#v}" -ge 2 ]; then
    case "$v" in
      \"*\") v="${v:1:${#v}-2}" ;;
      \'*\') v="${v:1:${#v}-2}" ;;
    esac
  fi
  printf '%s' "$v"
}

env_value() {  # env_value <file> <KEY> -> normalized value (never printed by callers)
  local line
  line="$(grep -E "^[[:space:]]*(export[[:space:]]+)?$2[[:space:]]*=" "$1" 2>/dev/null | tail -1 || true)"
  normalize "${line#*=}"
}

check_secrets_distinct() {
  # Production's .env is REQUIRED: without it we cannot prove staging differs.
  # The old staging .env is optional (it may be removed once that stack retires).
  local f key mine theirs
  [ -e "$PROD_DIR/.env" ] || die "production env $PROD_DIR/.env not found; cannot prove staging secrets differ"
  for f in "$PROD_DIR/.env" "$OLD_STAGING_DIR/.env"; do
    if [ ! -e "$f" ]; then
      echo "  --  $f not present (optional), skipped"
      continue
    fi
    [ -r "$f" ] || die "cannot read $f (run deploy.sh with sudo); refusing to skip the check"
    for key in SECRET_KEY POSTGRES_PASSWORD POSTGRES_DB POSTGRES_USER; do
      mine="$(normalize "${!key:-}")"
      theirs="$(env_value "$f" "$key")"
      [ -n "$mine" ] || die "$key is empty in staging .env"
      [ "$mine" != "$theirs" ] || die "$key equals the value in $f - generate a new one"
    done
  done
  case "$SECRET_KEY$POSTGRES_PASSWORD" in *__generate__*) die "placeholder secrets still in .env";; esac
  [ "${#SECRET_KEY}" -ge 50 ] || die "SECRET_KEY must be at least 50 characters"
  echo "  ok  secrets differ from production and old staging"
}

check_image() {  # check_image <ref>
  local ref="$1"
  case "$ref" in
    *:latest|*:latest@*|"") die "image '$ref' is empty or :latest" ;;
    tinotenda762/*) die "image '$ref' is in the production repository namespace" ;;
    *__sha__*) die "image '$ref' still has the placeholder tag" ;;
  esac
  docker image inspect "$ref" >/dev/null 2>&1 \
    || die "image '$ref' is not loaded on this host (build off-VM, then docker save | ssh erp-vm docker load)"
}

bundle_guardrail() {  # bundle_guardrail <image> <required-origin>
  local image="$1" required="$2" bundle o
  bundle="$(docker run --rm --network none --entrypoint sh "$image" \
    -c 'cat /usr/share/nginx/html/assets/*.js')" || die "cannot read bundle of $image"
  for o in "${FORBIDDEN_ORIGINS[@]}"; do
    if grep -qF "$o" <<<"$bundle"; then
      die "bundle of $image contains forbidden origin '$o' (production or default); rebuild with --build-arg VITE_API_URL"
    fi
  done
  grep -qF "$required" <<<"$bundle" || die "bundle of $image does not contain the staging API origin '$required'"
  echo "  ok  bundle guardrail $image"
}

wait_healthy() {  # wait_healthy <service> <timeout-seconds>
  local svc="$1" t="$2" id state
  id="$("${COMPOSE[@]}" ps -q "$svc")"
  [ -n "$id" ] || die "service $svc has no container"
  # A container with a healthcheck must reach "healthy"; "running" is accepted
  # only for a container that defines no healthcheck at all.
  for _ in $(seq "$t"); do
    state="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}nohc:{{.State.Status}}{{end}}' "$id")"
    case "$state" in
      healthy) echo "  ok  $svc healthy"; return 0 ;;
      nohc:running) echo "  ok  $svc running (no healthcheck defined)"; return 0 ;;
    esac
    sleep 1
  done
  die "$svc not healthy after ${t}s (state: $state); see ./deploy.sh logs $svc"
}

# --- actions -------------------------------------------------------------------
cmd="${1:-}"
case "$cmd" in
  up)
    echo "== erp-staging up"
    check_secrets_distinct
    check_image "$API_IMAGE"
    check_image "$FRONTEND_IMAGE"
    check_image "$PORTAL_IMAGE"
    bundle_guardrail "$FRONTEND_IMAGE" "${STAGING_FRONTEND_API_ORIGIN:?STAGING_FRONTEND_API_ORIGIN must be set}"
    bundle_guardrail "$PORTAL_IMAGE" "${STAGING_PORTAL_API_ORIGIN:?STAGING_PORTAL_API_ORIGIN must be set}"
    "${COMPOSE[@]}" config -q || die "compose config invalid"

    "$DIR/preflight.sh" check
    SNAP="$(mktemp "$DIR/.prod-snapshot.XXXXXX")"
    trap 'rm -f "$SNAP"' EXIT
    "$DIR/preflight.sh" snapshot "$SNAP"

    "${COMPOSE[@]}" up -d --pull never --no-build db api
    wait_healthy db 60
    wait_healthy api 180
    "${COMPOSE[@]}" up -d --pull never --no-build frontend portal
    wait_healthy frontend 60
    wait_healthy portal 60

    "$DIR/preflight.sh" verify "$SNAP"
    echo "== erp-staging up: done"
    "${COMPOSE[@]}" ps
    ;;
  stop)
    SNAP="$(mktemp "$DIR/.prod-snapshot.XXXXXX")"
    trap 'rm -f "$SNAP"' EXIT
    "$DIR/preflight.sh" snapshot "$SNAP"
    "${COMPOSE[@]}" stop
    "$DIR/preflight.sh" verify "$SNAP"
    ;;
  status) "${COMPOSE[@]}" ps ;;
  logs) shift; "${COMPOSE[@]}" logs --tail 200 "$@" ;;
  *) die "usage: deploy.sh up | stop | status | logs [service]" ;;
esac

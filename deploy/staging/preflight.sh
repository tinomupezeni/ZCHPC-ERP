#!/usr/bin/env bash
# =============================================================================
# erp-staging preflight - read-only safety checks around every staging action.
#
#   preflight.sh check              host checks before starting/updating staging
#   preflight.sh snapshot <file>    record production's containers/volumes/network
#   preflight.sh verify <file>      fail if production changed since the snapshot
#
# Exit code 0 = safe, non-zero = abort. This script never changes anything.
# =============================================================================
set -euo pipefail

PROD_PROJECT="zchpc-erp"
OLD_STAGING_PROJECT="zchpc-erp-staging"
PROD_CONTAINERS=(zchpc_db zchpc_api zchpc_frontend zchpc_portal)
MIN_AVAILABLE_KB=$((1536 * 1024))   # 1.5 GiB
MIN_DISK_FREE_KB=$((5 * 1024 * 1024))   # 5 GiB
RESERVED_PORTS=(8000 3000 3001 5432 5440 8001 3010 3011)

die() { echo "PREFLIGHT ABORT: $*" >&2; exit 1; }
ok() { echo "  ok  $*"; }

prod_state() {
  # One line per production container: name id started image restart-count running.
  local c
  for c in "${PROD_CONTAINERS[@]}"; do
    docker inspect -f '{{.Name}} {{.Id}} {{.State.StartedAt}} {{.Image}} {{.RestartCount}} {{.State.Running}}' "$c" 2>/dev/null \
      || echo "/$c MISSING"
  done
  echo "--- volumes"
  docker volume ls -q --filter "label=com.docker.compose.project=${PROD_PROJECT}" | sort
  echo "--- network"
  docker network ls -q --filter "label=com.docker.compose.project=${PROD_PROJECT}" | sort
}

check() {
  echo "preflight: host checks"

  # 1. Production must be up: staging must never start while production's
  #    ports are free (cPanel would route public traffic to whatever binds them).
  local c running
  for c in "${PROD_CONTAINERS[@]}"; do
    running=$(docker inspect -f '{{.State.Running}}' "$c" 2>/dev/null || echo missing)
    [ "$running" = "true" ] || die "production container $c is not running ($running); refusing to touch staging"
  done
  ok "production containers running"

  # 2. The old staging stack (shares production secrets, see AUDIT.md §9 C1-C3)
  #    must be stopped before this stack starts.
  local old
  old=$(docker ps -q --filter "label=com.docker.compose.project=${OLD_STAGING_PROJECT}")
  [ -z "$old" ] || die "old staging stack '${OLD_STAGING_PROJECT}' is still running ($(echo "$old" | wc -l) containers); stop it first (needs owner approval)"
  ok "old staging stack '${OLD_STAGING_PROJECT}' not running"

  # 3. Memory: swap is already in use on this VM.
  local avail
  avail=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
  [ "${avail:-0}" -ge "$MIN_AVAILABLE_KB" ] \
    || die "MemAvailable is $((avail / 1024)) MiB, need at least $((MIN_AVAILABLE_KB / 1024)) MiB"
  ok "MemAvailable $((avail / 1024)) MiB"

  # 4. Disk, on Docker's own data root (snap Docker uses
  #    /var/snap/docker/common/var-lib-docker, not /var/lib/docker).
  local free root
  root=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null) || die "cannot read Docker's data root (docker info)"
  [ -n "$root" ] || die "docker info returned an empty DockerRootDir"
  free=$(df -Pk "$root" 2>/dev/null | awk 'NR==2 {print $4}') || die "cannot read free space on $root"
  [ "${free:-0}" -ge "$MIN_DISK_FREE_KB" ] || die "only $((free / 1024)) MiB free on $root"
  ok "disk free $((free / 1024 / 1024)) GiB"

  # 5. Staging ports must not be any production/old-staging port, and must be
  #    free unless already held by erp-staging itself.
  local p owner
  for p in "${STAGING_API_PORT:-18000}" "${STAGING_FRONTEND_PORT:-13000}" "${STAGING_PORTAL_PORT:-13001}"; do
    for r in "${RESERVED_PORTS[@]}"; do
      [ "$p" != "$r" ] || die "staging port $p collides with reserved production/old-staging port"
    done
    if ss -Htln "sport = :$p" | grep -q .; then
      owner=$(docker ps --filter "publish=$p" --format '{{.Label "com.docker.compose.project"}}')
      [ "$owner" = "erp-staging" ] || die "port $p is in use by '${owner:-a non-docker process}'"
    fi
  done
  ok "staging ports free or owned by erp-staging"
}

case "${1:-}" in
  check) check ;;
  snapshot)
    [ -n "${2:-}" ] || die "usage: preflight.sh snapshot <file>"
    prod_state > "$2"
    grep -q MISSING "$2" && die "production container missing at snapshot time"
    echo "preflight: production snapshot written to $2"
    ;;
  verify)
    [ -f "${2:-}" ] || die "usage: preflight.sh verify <snapshot-file>"
    if ! diff -u "$2" <(prod_state); then
      die "PRODUCTION CHANGED during the staging action (diff above). Investigate immediately."
    fi
    echo "preflight: production unchanged (container ids, start times, images, volumes, network)"
    ;;
  *) die "usage: preflight.sh check | snapshot <file> | verify <file>" ;;
esac

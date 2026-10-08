#!/usr/bin/env bash
# =============================================================================
# erp-staging evaluation seed - loads EVALUATION data into the erp-staging
# database only. Never restores production data; never touches another project.
#
#   sudo ./seed-eval.sh          (run after `./deploy.sh up`; idempotent)
#
# Guards (any failure aborts before writing):
#   - .env identity is erp-staging / staging, file is chmod 600
#   - the api and db containers carry compose project label erp-staging
#   - inside the api container: ZCHPC_ENV=staging, DB_HOST=db, DB_NAME=$POSTGRES_DB
#   - the database is either empty (no employees) or already carries the
#     evaluation-seed marker (COMMENT ON DATABASE ... 'zchpc-eval-seed')
#
# Seeding: uses `manage.py seed_evaluation` when it exists (AUDIT.md blocker #2);
# until then the interim seed below. Every seeded login then gets a freshly
# generated password, written ONLY to ./credentials.txt (chmod 600) - nothing
# is printed. Hard-coded seed passwords ('admin', 'testpass123') never survive.
# =============================================================================
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="erp-staging"
MARKER="zchpc-eval-seed"
CREDS="$DIR/credentials.txt"

# Logins created by the interim seed (seed_admin + seed_pr_test_data).
ACCOUNTS=(
  "admin@zchpc.ac.zw|System administrator (superuser)"
  "riley.requester@example.com|PR requester (EC EMP via portal)"
  "hana.head@example.com|PR department head (IT)"
  "adam.accounts@example.com|PR accounts"
  "gina.manager@example.com|PR general manager"
  "dana.director@example.com|PR director"
  "pat.procure@example.com|PR procurement officer"
)

die() { echo "SEED ABORT: $*" >&2; exit 1; }

# --- 1. identity ----------------------------------------------------------------
[ -f "$DIR/.env" ] || die "missing $DIR/.env"
[ "$(stat -c %a "$DIR/.env")" = "600" ] || die "$DIR/.env must be chmod 600"
set -a
# shellcheck disable=SC1091
. "$DIR/.env"
set +a
[ "${COMPOSE_PROJECT_NAME:-}" = "$PROJECT" ] || die "COMPOSE_PROJECT_NAME must be $PROJECT"
[ "${ZCHPC_ENV:-}" = "staging" ] || die "ZCHPC_ENV must be staging"
[ -n "${POSTGRES_DB:-}" ] && [ -n "${POSTGRES_USER:-}" ] || die "POSTGRES_DB/POSTGRES_USER must be set"

COMPOSE=(docker compose -p "$PROJECT" -f "$DIR/docker-compose.yml" --env-file "$DIR/.env")

# --- 2. resolve and verify containers -------------------------------------------
API="$("${COMPOSE[@]}" ps -q api)"
DB="$("${COMPOSE[@]}" ps -q db)"
[ -n "$API" ] && [ -n "$DB" ] || die "api/db not running; run ./deploy.sh up first"
for c in "$API" "$DB"; do
  label="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$c")"
  [ "$label" = "$PROJECT" ] || die "container $c belongs to project '$label', not $PROJECT"
done

in_api_env() { docker exec "$API" printenv "$1" 2>/dev/null || true; }
[ "$(in_api_env ZCHPC_ENV)" = "staging" ] || die "api container is not ZCHPC_ENV=staging"
[ "$(in_api_env DB_HOST)" = "db" ] || die "api container DB_HOST is not 'db'"
[ "$(in_api_env DB_NAME)" = "$POSTGRES_DB" ] || die "api container DB_NAME does not match staging POSTGRES_DB"

psql_db() { docker exec -i "$DB" psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAq "$@"; }

# --- 3. empty-or-marked database guard -----------------------------------------
marker="$(psql_db -c "SELECT coalesce(shobj_description(oid, 'pg_database'), '') FROM pg_database WHERE datname = current_database();")"
employees="$(psql_db -c "SELECT count(*) FROM hr_employees;" 2>/dev/null)" \
  || die "hr_employees not found; the api container migrates on start - check ./deploy.sh logs api"
if [ "$marker" != "$MARKER" ] && [ "$employees" != "0" ]; then
  die "database has $employees employees and no '$MARKER' marker; refusing to seed a database this script did not create"
fi
psql_db -c "COMMENT ON DATABASE \"$POSTGRES_DB\" IS '$MARKER';"
echo "  ok  database empty or seed-marked; marker set"

# --- 4. seed ---------------------------------------------------------------------
manage() { docker exec "$API" python manage.py "$@"; }
quiet() {  # run a seed command, hiding any line that mentions a password
  local out rc=0
  out="$(manage "$@" 2>&1)" || rc=$?
  grep -viE 'password|passwd' <<<"$out" || true
  [ "$rc" -eq 0 ] || die "manage.py $* failed (exit $rc)"
}

if manage help seed_evaluation >/dev/null 2>&1; then
  echo "== seed_evaluation"
  quiet seed_evaluation
else
  echo "== interim seed (seed_evaluation not available yet)"
  quiet seed_admin
  quiet seed_purchase_request_categories
  quiet import_chart_of_accounts
  quiet seed_pr_test_data
  quiet seed_test_jobs
fi

# --- 5. replace every known seed password with a generated one ------------------
umask 077
gen() { head -c 32 /dev/urandom | base64 | tr -d '/+=\n' | head -c 20; }

CREDS_TMP="$(mktemp "$DIR/.credentials.XXXXXX")"
trap 'rm -f "$CREDS_TMP"' EXIT

# Build one Django shell script: it first checks that EVERY account exists and
# exits 3 without changing anything if one is missing; only then sets passwords.
pairs=""
for entry in "${ACCOUNTS[@]}"; do
  email="${entry%%|*}"
  label="${entry#*|}"
  pw="$(gen)"
  pairs+="    ('$email', '$pw'),
"
  printf '%-32s %-20s %s\n' "$email" "$pw" "$label" >> "$CREDS_TMP"
done
script="import sys
from django.contrib.auth import get_user_model
from django.db import transaction
U = get_user_model()
pairs = [
$pairs]
missing = [e for e, _ in pairs if not U.objects.filter(email=e).exists()]
if missing:
    print('SEED_MISSING:' + ','.join(missing))
    sys.exit(3)
with transaction.atomic():
    for e, p in pairs:
        u = U.objects.get(email=e)
        u.set_password(p)
        u.save(update_fields=['password'])
print('SEED_PASSWORDS_SET:%d' % len(pairs))
"
# Passwords travel over stdin, never argv, so they do not appear in `ps`.
rc=0
result="$(printf '%s' "$script" | docker exec -i "$API" python manage.py shell 2>&1)" || rc=$?
if [ "$rc" -ne 0 ] || ! grep -q '^SEED_PASSWORDS_SET:' <<<"$result"; then
  missing="$(grep -o '^SEED_MISSING:.*' <<<"$result" | cut -d: -f2- || true)"
  [ -n "$missing" ] && die "seeded accounts missing: $missing (no passwords changed, credentials.txt not written)"
  die "password rotation failed (exit $rc); no credentials.txt written: $(grep -viE 'password|passwd' <<<"$result" | tail -3)"
fi
mv "$CREDS_TMP" "$CREDS"
chmod 600 "$CREDS"
trap - EXIT
echo "  ok  passwords rotated for ${#ACCOUNTS[@]} accounts; credentials in $CREDS (chmod 600, not printed)"
echo "== seed complete"

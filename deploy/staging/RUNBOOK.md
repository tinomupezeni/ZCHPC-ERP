# erp-staging runbook: deploy and reseed

How to redeploy the isolated staging stack (`erp-staging`, on `erp-vm` 10.50.14.12, next to production) from one
commit of `master`, and reseed it with the evaluation data. Steps 0–2 are exactly as run on Sun 2026-10-11 (Day 4,
commit 7246917). Step 3 (the VM) was first run on Mon 2026-10-12 for 128c60d and corrected to what happened (run
log at the end).
Production (`zchpc-erp`, ports 8000/3000/3001) must never change. Every step that changes the VM is shown first and
done only when the owner says yes.

Conventions:
- `<SHA>` is the short commit id being deployed (`git rev-parse --short origin/master`).
- `<VM>` is `10.50.14.12`. Staging ports: API 18000, synergy 13000, portal 13001.
- Laptop commands run in Git Bash. On Windows, use `C:\Windows\System32\OpenSSH\ssh.exe` (Git Bash's own ssh fails
  auth); the host alias is `erp-vm`.
- VM commands run in `/home/user/erp-staging` unless stated.

## 0. Before you start

- [ ] `master` is the commit you mean to ship: `git fetch origin && git log --oneline -1 origin/master`.
- [ ] Nothing else is using the VM's memory heavily (preflight refuses below 1.5 GiB available).

## 1. Tests, on the exact commit (laptop, Docker off)

Make an **LF** worktree of the commit. It is used for the tests and then for the build. A CRLF checkout gives
`entrypoint.sh` a CRLF shebang, and the api container then dies with "exec /app/entrypoint.sh: no such file or directory".

```bash
SHA=$(git rev-parse --short origin/master)
WT=<scratch dir>/rel
git -c core.autocrlf=false worktree add --detach "$WT" "$SHA"
cp erp_project/.env "$WT/erp_project/.env"     # settings need SECRET_KEY; removed again before the build
cd "$WT/erp_project"
PY=<repo>/.venv/Scripts/python.exe
export DB_NAME=erp_db_rel                       # own test DB; never shared with another run
$PY -m pytest tests/integration/modules/identity tests/integration/modules/hr tests/unit \
  --ignore=tests/integration/modules/identity/test_aud02_recon.py \
  --ignore=tests/integration/modules/identity/test_aud02_f3_recon.py -q -p no:cacheprovider -rfE
$PY -m pytest tests/integration/modules/procurement tests/integration/modules/attendance \
  tests/integration/modules/leave tests/integration/modules/payroll tests/integration/modules/recruitment \
  src/modules/portal/tests src/modules/procurement/tests -q -p no:cacheprovider -rfE
$PY -m pytest tests/integration/modules/portal -q -p no:cacheprovider -rfE
```

Compare the failures, test by test, with the baseline in PLAN.md (Day 4). Anything new: stop.

## 2. Build the three images (laptop, Docker on)

```bash
cd "$WT" && rm -f erp_project/.env       # never in a build context (.dockerignore also excludes it)
docker build --target production -t erp-staging/api:$SHA erp_project
docker build --build-arg VITE_API_URL=http://<VM>:18000 \
  --build-arg VITE_PORTAL_URL=http://<VM>:13001 \
  -t erp-staging/frontend:$SHA zchpc-erp-synergy-main
docker build --build-arg VITE_API_URL=http://<VM>:18000 -t erp-staging/portal:$SHA employee-portal
```

`VITE_API_URL` is the bare origin: no `/api`, no trailing slash. Both frontend Dockerfiles default to the
**production** origin, so a missing `--build-arg` bakes production in.

### Bundle guardrail (laptop)

In Git Bash, prefix each `docker run` below with `MSYS_NO_PATHCONV=1`, or Git Bash rewrites the container paths into
Windows paths.

This is the same check `deploy.sh up` runs on the VM. Each bundle must contain the staging API origin, and must
contain none of the production or default origins.

```bash
for img in erp-staging/frontend:$SHA erp-staging/portal:$SHA; do
  b=$(docker run --rm --network none --entrypoint sh "$img" -c 'cat /usr/share/nginx/html/assets/*.js')
  for o in zchpcerp.zchpc.ac.zw employees.zchpc.ac.zw localhost:8000 10.50.14.12:8000 10.50.14.12:8001; do
    grep -qF "$o" <<<"$b" && echo "FAIL $img contains $o"
  done
  grep -qF "http://<VM>:18000" <<<"$b" && echo "ok   $img has the staging API origin" || echo "FAIL $img lacks it"
done
docker run --rm --entrypoint sh erp-staging/api:$SHA -c 'head -c 20 /app/entrypoint.sh | od -c | head -2'  # no \r
```

Save the images to a file, then quit Docker Desktop:

```bash
docker save erp-staging/api:$SHA erp-staging/frontend:$SHA erp-staging/portal:$SHA | gzip > erp-staging-$SHA.tar.gz
gzip -t erp-staging-$SHA.tar.gz && sha256sum erp-staging-$SHA.tar.gz     # compare on the VM after the copy
```
(2026-10-11, 7246917: about 141 MB.)

## 3. On the VM (each changing command needs the owner's yes)

**Read-only checks first** (change nothing; run them before 3a and report):
```bash
./preflight.sh check
sha256sum deploy.sh preflight.sh seed-eval.sh docker-compose.yml          # compare with the worktree
grep -E '^[A-Z_]*(IMAGE|URL|ORIGIN|HOSTS|PORT)[A-Z_]*=' .env | grep -viE 'pass|secret|key|token|database_url'
docker ps -a --filter label=com.docker.compose.project=erp-staging
docker volume ls --filter label=com.docker.compose.project=erp-staging
docker image ls 'erp-staging/*'; docker image ls postgres                 # postgres:16-alpine must be present
```
`docker volume ls --filter name=erp-staging` matches **substrings**, so it also lists the old stack's
`zchpc-erp-staging_*` volumes. Never use its output as a list of things to remove.

**a. Production snapshot** (read-only):
```bash
./preflight.sh check
./preflight.sh snapshot ~/prod-snapshot-<date>.txt
```

**b. Deploy files from `master`.** Copy `deploy/staging/{deploy.sh,preflight.sh,seed-eval.sh,docker-compose.yml}`
from the worktree to `/home/user/erp-staging/`. `.env` is never copied over. Then check they match:
```bash
sha256sum deploy.sh preflight.sh seed-eval.sh docker-compose.yml    # on the VM
sha256sum deploy/staging/{deploy.sh,preflight.sh,seed-eval.sh,docker-compose.yml}   # in the LF worktree
```

**c. Transfer and load the images:**
```bash
scp erp-staging-$SHA.tar.gz erp-vm:/home/user/            # laptop
gunzip -c ~/erp-staging-$SHA.tar.gz | docker load          # VM
docker image ls 'erp-staging/*'
```

**d. Stop staging** (staging only; containers and volumes kept; production snapshot verified; no sudo needed):
```bash
./deploy.sh stop
```

**e. Reset the staging database (only when a fresh seed is wanted).** Remove exactly one volume, by its exact name,
with no prune and no wildcard. Show the command to the owner first, and run it only after an explicit "yes":
```bash
docker volume inspect -f '{{index .Labels "com.docker.compose.project"}}' erp-staging_db_data   # must print erp-staging
docker ps -a --filter volume=erp-staging_db_data --format '{{.Names}}|{{.State}}'             # must be erp-staging-db-1|exited
docker rm erp-staging-db-1            # stopped containers still hold their volume; no -f, no -v
docker volume rm erp-staging_db_data
docker volume ls --filter label=com.docker.compose.project=erp-staging                          # api_media, api_static left
```

**f. Point `.env` at the new images:**
```bash
cp -p .env .env.bak-<old sha>          # stays chmod 600
grep _IMAGE .env
sed -i 's#^\(API_IMAGE=erp-staging/api:\).*#\1<SHA>#; s#^\(FRONTEND_IMAGE=erp-staging/frontend:\).*#\1<SHA>#; s#^\(PORTAL_IMAGE=erp-staging/portal:\).*#\1<SHA>#' .env
grep _IMAGE .env
```

**g. Start (owner, needs sudo):** `sudo ./deploy.sh up`. It checks secrets, images and both bundles, then runs
preflight, starts db+api (the migrations run in the api entrypoint), then the frontends, and finally verifies that
production is unchanged.

**h. Seed (owner, needs sudo):** `sudo ./seed-eval.sh`. It writes the 8 passwords only to `credentials.txt`
(chmod 600). The seed command prints the EC numbers.

**i. Production unchanged:** `./preflight.sh verify ~/prod-snapshot-<date>.txt`.

## 4. Hand checks after a deploy

See PLAN.md Day 4 (first item) and §6. At minimum:
- every one of the 8 logins signs in
- portal refresh and logout work
- the portal dashboard loads
- synergy's sidebar survives a reload
- the hidden routes show "Not available in this evaluation"

## Run log: Mon 2026-10-12, 128c60d (first run of step 3)

Steps 1–2 were done Sun 2026-10-11 (see PLAN.md Day 4). Tar `erp-staging-128c60d.tar.gz`, 141,107,010 bytes, sha256
`71ac572e0ef3ec9a42a6708ddba9ba2b62a6372bc94f10346584adcc2180bfce`.

**Read-only checks (09:01):**
- `preflight.sh check` passes: production running, old stack stopped, MemAvailable 5501 MiB, disk 38 GiB free,
  ports OK.
- Deployed files: `preflight.sh` already matches 128c60d. `deploy.sh`, `seed-eval.sh` and `docker-compose.yml` still
  match 2ec500e (Friday's deploy). The 128c60d versions are identical to `master` f058806.
- `.env`: `*_IMAGE` = `:f70f026`. API origins `http://10.50.14.12:18000`; ports 18000/13000/13001. The new compose
  variables (`JWT_*_LIFETIME_*`) have empty defaults, so `.env` needs no new lines.
- Staging: 4 containers (db, api, frontend, portal), all f70f026 / postgres:16-alpine, all healthy. Volumes
  `erp-staging_{api_media,api_static,db_data}`. Images: only `:f70f026`; `postgres:16-alpine` is present.

**3a. Snapshot (09:04).** `preflight.sh check` passes again (MemAvailable 5498 MiB). Snapshot written to
`~/prod-snapshot-2026-10-12.txt`: 4 production containers, all running with 0 restarts (db started 09-25, the other
three 09-29). Volumes `zchpc-erp_{api_media,api_static,postgres_data}`, network `933b1338695f`.

**3b. Deploy files (09:09).** Friday's `deploy.sh`, `seed-eval.sh` and `docker-compose.yml` were backed up first to
`~/erp-staging-files-2ec500e/` (hashes = 2ec500e). Then the four files were copied with Windows `scp.exe` from the LF
worktree. On the VM the sha256s match 128c60d/master: deploy.sh `39aec8c6…`, preflight.sh `327c4c37…`, seed-eval.sh
`865c5551…`, docker-compose.yml `e6ef4334…`. No CR bytes; scripts still executable; `.env` and `credentials.txt`
untouched.
- Quoting note: a multi-command string passed to `ssh.exe` through `cmd /c "..."` arrives as **one** command name
  ("No such file or directory", nothing runs). Put multi-command steps in an LF script and send it with
  `cmd /c "ssh.exe erp-vm bash -s < script.sh"`.

**3c. Tar transfer (09:13).** `scp.exe` of `erp-staging-128c60d.tar.gz` to `/home/user/` over
the LAN. On the VM: 141,107,010 bytes, sha256 `71ac572e…bfce` (same as on the laptop), `gzip -t` ok.

**3d. Load (09:15, 16 s).** `gunzip -c ~/erp-staging-128c60d.tar.gz | docker load` loaded
`erp-staging/{api,frontend,portal}:128c60d` (IDs 889c2f4ab9c1, 00009d23b82c, be42d9cea488). The `:f70f026` tags stay
(still in use).

**Volume check before the stop (09:16, read-only).** `docker volume inspect erp-staging_db_data`: label
`com.docker.compose.project=erp-staging`, `com.docker.compose.volume=db_data`, created 2026-10-09 10:52 (Friday's
deploy). Only `erp-staging-db-1` uses it. Production's DB volume is `zchpc-erp_postgres_data` (project `zchpc-erp`).
Check the label before removing:
```bash
docker volume inspect -f '{{index .Labels "com.docker.compose.project"}}' erp-staging_db_data   # must print erp-staging
docker ps -a --filter volume=erp-staging_db_data     # only erp-staging-db-1
```

**3e. Stop (09:19, 6 s).** `./deploy.sh stop` ran **without sudo** (user is in the `docker` group and owns `.env`).
Stopped in order portal, frontend, api, db; all four now `Exited (0)`, containers kept. deploy.sh's own snapshot and
verify passed ("production unchanged"), and so did `preflight.sh verify ~/prod-snapshot-2026-10-12.txt`.
**Note for 3f:** `stop` keeps the containers, and a stopped container still holds its volume, so
`docker volume rm erp-staging_db_data` alone fails with "volume is in use". Remove the stopped db container first
(`docker rm erp-staging-db-1`, no `-f`, no `-v`); `deploy.sh up` recreates it.

**3f. DB reset (09:21, owner said yes).** One `set -eu` script with two guards: the volume's project label must be
`erp-staging`, and its only user must be `erp-staging-db-1|exited`; otherwise abort. Both passed. Then
`docker rm erp-staging-db-1` and `docker volume rm erp-staging_db_data`. Left: volumes
`erp-staging_{api_media,api_static}`; containers api, frontend and portal (exited). `preflight.sh verify` against the
morning snapshot: production unchanged.

**3g. `.env` tags (09:22).** Backed up first with `cp -p .env .env.bak-f70f026` (stays 600). The `sed` above changed
exactly 3 lines (36–38), `:f70f026` → `:128c60d`; `.env` still `600 user`. All three `:128c60d` images are present.
To roll back to Friday: `cp -p .env.bak-f70f026 .env` (but the f70f026 DB volume is gone, so reseed either way).

**3h. `sudo ./deploy.sh up` (owner, ~09:25).** Finished without abort. Checks afterwards (09:27, read-only):
- 4 containers healthy on `:128c60d` / postgres:16-alpine; new `erp-staging_db_data` created 09:25, label
  `erp-staging`.
- api log: 95 migrations applied OK on the empty DB, including hr.0021–0025; `showmigrations --plan`: 0 unapplied;
  gunicorn up with 2 workers. No errors (a grep for "error" also hits the migration *named*
  `auth.0007_alter_validators_add_error_messages`; that is not an error).
- HTTP from the VM: API `/` 404 (same as production's `/`), `/api/` 401, `/admin/login/` 200; synergy :13000 200;
  portal :13001 200. Production :8000/:3000/:3001 answer as before.
- `preflight.sh verify ~/prod-snapshot-2026-10-12.txt`: production unchanged.

**3i. `sudo ./seed-eval.sh` (owner, ~09:29).** Finished without abort. Checks afterwards (09:30, read-only; the
credentials file was not read):
- DB comment = `zchpc-eval-seed`; 20 employees; 20 users, all active.
- The 8 logins exist, active, with usable passwords; only admin is superuser. Roles (on `hr_employees.role_id` →
  `hr_role`, not on the user): EMP0001 admin ADMIN, EMP0002 HUMAN_RESOURCES, EMP0003 DEPARTMENT_MANAGER,
  EMP0004 ACCOUNTANT, EMP0005 GENERAL_MANAGER, EMP0006 DIRECTOR, EMP0007 PROCUREMENT_OFFICER, EMP0008 REGULAR_STAFF.
  Across all 20: DEPARTMENT_MANAGER 6, REGULAR_STAFF 8, one each of the other six.
- `credentials.txt`: `600 root`, rewritten 09:29; no `.credentials.*` temp file left.
- 4 containers healthy; `preflight.sh verify ~/prod-snapshot-2026-10-12.txt`: production unchanged.
- Check-script gotcha: inside a script sent with `ssh ... bash -s < file`, `docker exec -i` reads the rest of the
  script from stdin. Give such calls `</dev/null` (or drop `-i`).

**Cleanup (owner's yes, after the hand checks):** removed by exact name, no prune, after checking no container used
them: images `erp-staging/{api,frontend,portal}:f70f026`, `~/erp-staging-128c60d.tar.gz`, `~/erp-staging-5d95274.tar.gz`.
**Left on the VM:** the `:5d95274` images (in use), the `:128c60d` images (rollback), `.env.bak-128c60d`,
`.env.bak-f70f026`, `~/erp-staging-files-2ec500e/`, the two prod snapshots.

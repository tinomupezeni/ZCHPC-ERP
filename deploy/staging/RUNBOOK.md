# erp-staging runbook: deploy and reseed

How to redeploy the isolated staging stack (`erp-staging`, on `erp-vm` 10.50.14.12, next to production) from one
commit of `master`, and reseed it with the evaluation data. Steps 0–2 are exactly as run on Sun 2026-10-11 (Day 4,
commit 7246917). Step 3 (the VM) is written from `deploy.sh`/`preflight.sh` and has not been run yet; it is corrected
to what actually happens on the first run.
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

**d. Stop staging** (staging only; volumes kept; production snapshot verified):
```bash
./deploy.sh stop
```

**e. Reset the staging database (only when a fresh seed is wanted).** Remove exactly one volume, by its exact name,
with no prune and no wildcard. Show the command to the owner first, and run it only after an explicit "yes":
```bash
docker volume ls --filter name=erp-staging_db_data
docker volume rm erp-staging_db_data
```

**f. Point `.env` at the new images:**
```bash
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

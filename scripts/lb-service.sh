#!/usr/bin/env bash
# Copyright 2025 Kamesh Sampath <kamesh.sampath@hotmail.com>
# SPDX-License-Identifier: Apache-2.0
#
# Refresh the Lakebase OAuth credential into ~/.pgpass and ~/.pg_service.conf.
#
# The Lakebase token expires after 1 hour, so re-run this whenever psql reports an
# auth failure. Afterwards use:  psql "service=<name>"   (no PGPASSWORD needed;
# the service entry points at passfile=~/.pgpass, which must be chmod 600).
#
# Usage: scripts/lb-service.sh [service-name]     (default: lakebase-demo)
# Env (from .env): LAKEBASE_PROJECT, LAKEBASE_BRANCH, DATABRICKS_PROFILE
# Optional: ENDPOINT (default: primary, the auto-created read-write endpoint)
set -euo pipefail

: "${LAKEBASE_PROJECT:?set LAKEBASE_PROJECT in .env}"
: "${LAKEBASE_BRANCH:?set LAKEBASE_BRANCH in .env}"
ENDPOINT="${ENDPOINT:-primary}"
SERVICE="${1:-lakebase-demo}"
PROFILE="${DATABRICKS_PROFILE:-DEFAULT}"

USER_EMAIL=$(databricks current-user me --profile "$PROFILE" --output json | jq -r .userName)

EP_PATH="projects/$LAKEBASE_PROJECT/branches/$LAKEBASE_BRANCH/endpoints/$ENDPOINT"

# The credential response carries the OAuth token (plus endpoint/ttl/expire_time),
# NOT host/port/database. Host comes from the endpoint resource, the database from
# list-databases, port is fixed at 5432.
cred=$(databricks postgres generate-database-credential "$EP_PATH" --profile "$PROFILE" --output json)
token=$(jq -r '.token // .response.token // empty' <<<"$cred")

ep=$(databricks postgres get-endpoint "$EP_PATH" --profile "$PROFILE" --output json)
host=$(jq -r '.status.hosts.host // .status.host // .host // empty' <<<"$ep")
port=5432

dbs=$(databricks postgres list-databases \
  "projects/$LAKEBASE_PROJECT/branches/$LAKEBASE_BRANCH" --profile "$PROFILE" --output json)
db=$(jq -r 'if .databases then (.databases[0].name // empty) elif (.[0] | type) == "object" then (.[0].name // .[0].database // empty) else .[0] end // "databricks_postgres"' <<<"$dbs")

if [[ -z "$token" || -z "$host" ]]; then
  echo "ERROR: could not extract token/host from API responses." >&2
  echo "credential keys: $(jq -r 'keys | join(", ")' <<<"$cred")" >&2
  echo "endpoint keys:   $(jq -r 'keys | join(", ")' <<<"$ep")" >&2
  exit 1
fi

passfile="${PGPASSFILE:-$HOME/.pgpass}"
touch "$passfile"
chmod 600 "$passfile"
# replace any existing line for this host, then append the fresh token
grep -v "^${host}:" "$passfile" > "$passfile.tmp" 2>/dev/null || true
mv "$passfile.tmp" "$passfile"
printf '%s:%s:%s:%s:%s\n' "$host" "$port" "$db" "$USER_EMAIL" "$token" >> "$passfile"

svc="${PGSERVICEFILE:-$HOME/.pg_service.conf}"
touch "$svc"
# drop any existing block for this service, then append a fresh one
awk -v s="$SERVICE" '$0 == "[" s "]" { skip = 1; next }
                    /^\[/ { skip = 0 }
                    !skip { print }' "$svc" > "$svc.tmp" || true
mv "$svc.tmp" "$svc"
cat >> "$svc" <<EOF
[$SERVICE]
host=$host
port=$port
dbname=$db
user=$USER_EMAIL
passfile=$passfile
sslmode=require
EOF

echo "service '$SERVICE' ready (host=$host db=$db user=$USER_EMAIL)"
echo "use:  psql \"service=$SERVICE\" -c 'SELECT 1;'"
echo "token expires in 1h; re-run this script to refresh (never commit $passfile)"

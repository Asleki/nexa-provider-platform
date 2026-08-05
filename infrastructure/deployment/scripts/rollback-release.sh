#!/usr/bin/env bash
set -euo pipefail
BASE=/opt/nexa/infrastructure-api
[[ -L "$BASE/previous" ]] || { echo "previous release is unavailable" >&2; exit 2; }
FROM=$(readlink -f "$BASE/current")
TO=$(readlink -f "$BASE/previous")
[[ "$FROM" != "$TO" ]] || { echo "current and previous releases are identical" >&2; exit 2; }
ln -sfn "$TO" "$BASE/current"
ln -sfn "$FROM" "$BASE/previous"
systemctl restart nexa-infrastructure-api
sleep 2
curl --fail --silent http://127.0.0.1:8000/api/v1/health/live >/dev/null
printf '{"rollbackId":"rollback:%s","fromRelease":"%s","toRelease":"%s","outcome":"passed","databaseWritesPerformed":0}\n' "$(date +%s)" "$FROM" "$TO"

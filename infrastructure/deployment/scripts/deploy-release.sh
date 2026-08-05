#!/usr/bin/env bash
set -euo pipefail
ARCHIVE=${1:?release archive required}
COMMIT_SHA=${2:?commit SHA required}
BASE=/opt/nexa/infrastructure-api
RELEASE="$BASE/releases/$COMMIT_SHA"
[[ "$COMMIT_SHA" =~ ^[0-9a-f]{7,40}$ ]] || { echo "invalid commit SHA" >&2; exit 2; }
[[ -f "$ARCHIVE" ]] || { echo "archive not found" >&2; exit 2; }
mkdir -p "$RELEASE"
tar -xzf "$ARCHIVE" -C "$RELEASE"
"$BASE/shared/venv/bin/pip" install -r "$RELEASE/infrastructure/requirements.txt"
PYTHONPATH="$RELEASE" "$BASE/shared/venv/bin/python" -m compileall -q "$RELEASE/infrastructure"
CURRENT_TARGET=$(readlink -f "$BASE/current" || true)
[[ -n "$CURRENT_TARGET" ]] && ln -sfn "$CURRENT_TARGET" "$BASE/previous"
ln -sfn "$RELEASE" "$BASE/current"
systemctl restart nexa-infrastructure-api
sleep 2
curl --fail --silent http://127.0.0.1:8000/api/v1/health/live >/dev/null || {
  [[ -L "$BASE/previous" ]] && ln -sfn "$(readlink -f "$BASE/previous")" "$BASE/current"
  systemctl restart nexa-infrastructure-api
  echo "deployment health check failed; previous release restored" >&2
  exit 3
}
echo "deployed release:$COMMIT_SHA"

#!/usr/bin/env bash
set -euo pipefail
ROOT=${1:-$(pwd)}
OUT=${2:-"$ROOT/dist"}
COMMIT_SHA=${COMMIT_SHA:-$(git -C "$ROOT" rev-parse HEAD)}
[[ "$COMMIT_SHA" =~ ^[0-9a-f]{7,40}$ ]] || { echo "invalid commit SHA" >&2; exit 2; }
mkdir -p "$OUT"
ARCHIVE="$OUT/infrastructure-api-$COMMIT_SHA.tar.gz"
tar -C "$ROOT" -czf "$ARCHIVE" infrastructure shared database registries services backend contracts
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
printf '%s\n' "$ARCHIVE"

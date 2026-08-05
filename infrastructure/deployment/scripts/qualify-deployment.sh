#!/usr/bin/env bash
set -euo pipefail
PUBLIC_URL=${1:-}
PYTHONPATH=. python -m infrastructure.deployment.qualification
systemctl is-active --quiet nexa-infrastructure-api
curl --fail --silent http://127.0.0.1:8000/api/v1/health/live >/dev/null
curl --fail --silent http://127.0.0.1:8000/api/v1/health/ready >/dev/null
if [[ -n "$PUBLIC_URL" ]]; then
  [[ "$PUBLIC_URL" == https://* ]] || { echo "public URL must use HTTPS" >&2; exit 2; }
  curl --fail --silent "$PUBLIC_URL/api/v1/health/live" >/dev/null
fi
echo "I006 deployment qualification passed"

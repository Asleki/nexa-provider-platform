#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then echo "run as root" >&2; exit 2; fi
id -u nexa-api >/dev/null 2>&1 || useradd --system --home /opt/nexa/infrastructure-api --shell /usr/sbin/nologin nexa-api
install -d -o nexa-api -g nexa-api /opt/nexa/infrastructure-api/{releases,shared}
python3 -m venv /opt/nexa/infrastructure-api/shared/venv
install -d -m 0750 /etc/nexa
install -m 0644 infrastructure/deployment/config/infrastructure-api.service /etc/systemd/system/nexa-infrastructure-api.service
systemctl daemon-reload
printf '%s\n' 'Bootstrap complete. Configure /etc/nexa/infrastructure-api.env and Caddy before deployment.'

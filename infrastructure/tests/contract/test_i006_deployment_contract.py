from pathlib import Path
import json

def root(): return Path(__file__).resolve().parents[3]

def test_systemd_and_caddy_keep_fastapi_private():
    service=(root()/"infrastructure/deployment/config/infrastructure-api.service").read_text()
    caddy=(root()/"infrastructure/deployment/config/Caddyfile.template").read_text()
    assert "--host 127.0.0.1" in service
    assert "EnvironmentFile=/etc/nexa/infrastructure-api.env" in service
    assert "reverse_proxy 127.0.0.1:8000" in caddy

def test_manifest_forbids_automatic_database_migrations():
    manifest=json.loads((root()/"infrastructure/deployment/manifests/deployment-manifest.json").read_text())
    assert manifest["milestoneId"] == "I006"
    assert manifest["databaseMigrationsAutomatic"] is False

def test_github_deployment_is_manual_only_and_has_no_database_secret_names():
    workflow=(root()/".github/workflows/deploy-infrastructure-api.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "push:" not in workflow
    assert "PGPASSWORD" not in workflow
    assert "INFRA_DEPLOY_SSH_KEY" in workflow

"""Static inspector for I006 deployment assets."""
from __future__ import annotations
from pathlib import Path
import json
from .contracts import DeploymentFinding

REQUIRED_FILES = (
    ".github/workflows/deploy-infrastructure-api.yml",
    "infrastructure/deployment/config/infrastructure-api.env.example",
    "infrastructure/deployment/config/infrastructure-api.service",
    "infrastructure/deployment/config/Caddyfile.template",
    "infrastructure/deployment/scripts/bootstrap-server.sh",
    "infrastructure/deployment/scripts/build-release.sh",
    "infrastructure/deployment/scripts/deploy-release.sh",
    "infrastructure/deployment/scripts/rollback-release.sh",
    "infrastructure/deployment/scripts/qualify-deployment.sh",
    "infrastructure/deployment/manifests/deployment-manifest.json",
)

class DeploymentSourceInspector:
    def __init__(self, repository_root: Path):
        self.root = repository_root.resolve()

    def inspect(self) -> tuple[DeploymentFinding, ...]:
        findings: list[DeploymentFinding] = []
        missing = [item for item in REQUIRED_FILES if not (self.root / item).is_file()]
        findings.append(DeploymentFinding("REQUIRED_FILES", not missing, "All required deployment assets exist." if not missing else f"Missing: {missing}"))
        env_text = (self.root / "infrastructure/deployment/config/infrastructure-api.env.example").read_text(encoding="utf-8")
        findings.append(DeploymentFinding("NO_REAL_SECRET_VALUES", "change-me" not in env_text.lower() and "PGPASSWORD=__SET_ON_SERVER_ONLY__" in env_text, "Environment template contains placeholders only."))
        service = (self.root / "infrastructure/deployment/config/infrastructure-api.service").read_text(encoding="utf-8")
        findings.append(DeploymentFinding("LOCAL_UVICORN_BIND", "--host 127.0.0.1" in service, "Uvicorn is bound to localhost."))
        caddy = (self.root / "infrastructure/deployment/config/Caddyfile.template").read_text(encoding="utf-8")
        findings.append(DeploymentFinding("CADDY_LOCAL_PROXY", "reverse_proxy 127.0.0.1:8000" in caddy, "Caddy proxies only to local Uvicorn."))
        workflow = (self.root / ".github/workflows/deploy-infrastructure-api.yml").read_text(encoding="utf-8")
        findings.append(DeploymentFinding("MANUAL_WORKFLOW", "workflow_dispatch:" in workflow and "push:" not in workflow, "Deployment workflow is manual-only."))
        manifest = json.loads((self.root / "infrastructure/deployment/manifests/deployment-manifest.json").read_text(encoding="utf-8"))
        findings.append(DeploymentFinding("MANIFEST_IDENTITY", manifest.get("milestoneId") == "I006" and manifest.get("databaseMigrationsAutomatic") is False, "Deployment manifest preserves I006 and migration boundaries."))
        shell_files = list((self.root / "infrastructure/deployment/scripts").glob("*.sh"))
        executable_headers = all(path.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash") for path in shell_files)
        findings.append(DeploymentFinding("SHELL_HEADERS", executable_headers, "All deployment scripts declare bash explicitly."))
        return tuple(findings)

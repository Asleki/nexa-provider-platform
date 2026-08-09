"""P006.UI.4-P006.UI.9 — Local-only development authentication HTTP authority."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse

from .development_service import AuthenticationRejected, DevelopmentAuthenticationService


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_service(root: Path | None = None) -> DevelopmentAuthenticationService:
    root = root or repository_root()
    private = root / "development" / "auth" / "private"
    return DevelopmentAuthenticationService(
        credential_dir=private / "credentials",
        catalogue_dir=private / "enigma",
    )


class DevelopmentAuthHandler(BaseHTTPRequestHandler):
    service: DevelopmentAuthenticationService

    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin", "")
        if not origin:
            return True
        try:
            parsed = urlparse(origin)
        except ValueError:
            return False
        return parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}

    def _cors(self):
        origin = self.headers.get("Origin")
        if origin and self._origin_allowed():
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _send(self, status: int, payload: dict):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0 or length > 16_384:
            raise AuthenticationRejected("invalid request body")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _bearer(self) -> str:
        value = self.headers.get("Authorization", "")
        if not value.startswith("Bearer "):
            raise AuthenticationRejected("missing session token")
        return value[7:].strip()

    def do_OPTIONS(self):
        if not self._origin_allowed():
            self._send(403, {"ok": False, "error": "origin_rejected"})
            return
        self.send_response(204)
        self._cors()
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self):
        if not self._origin_allowed():
            self._send(403, {"ok": False, "error": "origin_rejected"})
            return
        if self.path == "/health":
            self._send(200, {"ok": True, "service": "nexilabs-development-auth"})
            return
        if self.path == "/auth/session":
            try:
                self._send(200, {"ok": True, "session": self.service.session(self._bearer())})
            except AuthenticationRejected as exc:
                self._send(401, {"ok": False, "error": str(exc)})
            return
        self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        if not self._origin_allowed():
            self._send(403, {"ok": False, "error": "origin_rejected"})
            return
        try:
            if self.path == "/auth/guest/login":
                payload = self._read_json()
                session = self.service.login_guest(
                    username=payload.get("username", ""),
                    password=payload.get("password", ""),
                    runtime=payload.get("runtime", ""),
                )
                self._send(200, {"ok": True, "session": session})
                return
            if self.path == "/auth/developer/start":
                payload = self._read_json()
                result = self.service.start_developer(
                    username=payload.get("username", ""),
                    password=payload.get("password", ""),
                    runtime=payload.get("runtime", ""),
                )
                self._send(200, {"ok": True, **result})
                return
            if self.path == "/auth/developer/enigma":
                payload = self._read_json()
                session = self.service.verify_developer(
                    attempt_id=payload.get("attemptId", ""),
                    response=payload.get("response", ""),
                )
                self._send(200, {"ok": True, "session": session})
                return
            if self.path == "/auth/logout":
                revoked = self.service.logout(self._bearer())
                self._send(200, {"ok": True, "revoked": revoked})
                return
            self._send(404, {"ok": False, "error": "not_found"})
        except (AuthenticationRejected, json.JSONDecodeError) as exc:
            self._send(401, {"ok": False, "error": str(exc)})

    def log_message(self, format, *args):
        # Keep the local authority quiet unless explicitly wrapped with logging later.
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local NexiLabs development authentication authority.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    DevelopmentAuthHandler.service = build_service()
    server = ThreadingHTTPServer((args.host, args.port), DevelopmentAuthHandler)
    print(f"NexiLabs development auth listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

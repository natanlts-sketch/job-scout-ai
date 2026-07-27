"""Simple health check for deployment."""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.db import initialize_database  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path not in {"/", "/health", "/healthz"}:
            self.send_response(404)
            self.end_headers()
            return
        try:
            initialize_database()
            body = json.dumps({"status": "ok", "service": "job-scout-ai"}).encode()
            self.send_response(200)
        except Exception as exc:  # noqa: BLE001
            body = json.dumps({"status": "error", "detail": str(exc)}).encode()
            self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A003
        return


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Health server on :{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

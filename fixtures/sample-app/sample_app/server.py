"""Minimal HTTP server exposing GET /health on port 8080."""

from __future__ import annotations

import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"sample-app API listening on http://localhost:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

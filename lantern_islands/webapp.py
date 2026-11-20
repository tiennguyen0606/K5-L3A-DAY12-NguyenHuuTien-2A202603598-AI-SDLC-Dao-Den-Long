from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse

from .leaderboard import DEFAULT_PATH, LeaderboardStore


class GameHandler(SimpleHTTPRequestHandler):
    leaderboard = LeaderboardStore(DEFAULT_PATH)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="web", **kwargs)

    def _send_json(self, status: int, value: dict) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/leaderboard":
            self._send_json(200, {"entries": self.leaderboard.entries()})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/leaderboard":
            self._send_json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("invalid body size")
            payload = json.loads(self.rfile.read(length))
            entries = self.leaderboard.add(payload)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self._send_json(400, {"error": str(error)})
            return
        self._send_json(201, {"entries": entries})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--export-leaderboard", metavar="OUT")
    parser.add_argument("--data", default=str(DEFAULT_PATH))
    args = parser.parse_args(argv)
    GameHandler.leaderboard = LeaderboardStore(Path(args.data))
    if args.export_leaderboard:
        GameHandler.leaderboard.export(Path(args.export_leaderboard))
        return 0
    server = ThreadingHTTPServer((args.host, args.port), GameHandler)
    print(f"Dao Den Long: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

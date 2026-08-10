from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .aggregation import aggregate_all, aggregate_country
from .config import COUNTRIES
from .coverage import coverage_rows
from .db import database, read_database


WEB_ROOT = Path(__file__).resolve().parents[2] / "web"


class AtlasHandler(BaseHTTPRequestHandler):
    db_path: Path

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self._api(parsed.path, parse_qs(parsed.query))
            return
        relative = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
        candidate = (WEB_ROOT / relative).resolve()
        if WEB_ROOT.resolve() not in candidate.parents and candidate != WEB_ROOT.resolve():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _api(self, path: str, query: dict[str, list[str]]) -> None:
        try:
            year = int(query.get("year", ["2025"])[0])
            month_value = query.get("month", [""])[0]
            month = int(month_value) if month_value else None
            source = query.get("source", ["combined"])[0]
            if source not in {"energy-charts", "ember", "combined"}:
                raise ValueError("source must be 'energy-charts', 'ember' or 'combined'")
            with read_database(self.db_path) as connection:
                if path == "/api/health":
                    payload = {"status": "ok", "database": str(self.db_path)}
                elif path == "/api/countries":
                    payload = [country.__dict__ for country in COUNTRIES.values()]
                elif path == "/api/summary":
                    payload = aggregate_all(connection, year, month, source)
                elif path == "/api/compare":
                    codes = [code.upper() for code in query.get("countries", [""])[0].split(",") if code]
                    if not 2 <= len(codes) <= 4 or any(code not in COUNTRIES for code in codes):
                        raise ValueError("countries must contain 2 to 4 pilot country codes")
                    payload = [aggregate_country(connection, code, year, month, source) for code in codes]
                elif path == "/api/coverage":
                    payload = coverage_rows(connection, year)
                else:
                    self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                    return
            self._json(payload)
        except (ValueError, TypeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[http] {format % args}")


def create_server(db_path: Path, host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    db_path = Path(db_path)
    if not db_path.exists():
        with database(db_path):
            pass
    handler = type("ConfiguredAtlasHandler", (AtlasHandler,), {"db_path": db_path})
    return ThreadingHTTPServer((host, port), handler)


def serve(db_path: Path, host: str = "127.0.0.1", port: int = 8000) -> None:
    server = create_server(db_path, host, port)
    print(f"European Electricity Atlas: http://{host}:{port}")
    print(f"SQLite: {db_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

from __future__ import annotations

import json
import mimetypes
import os
import secrets
import time
from collections import defaultdict, deque
from http.cookies import SimpleCookie
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .aggregation import aggregate_all, aggregate_country, map_metric_dataset
from .config import COUNTRIES
from .coverage import coverage_rows
from .community import CommunityStore, browser_hash
from .country_profile import build_country_profile
from .db import database, read_database
from .metrics import metric_catalog
from .runtime import DEFAULT_COMMUNITY_DB, parse_public_origin, validate_existing_atlas_database
from .storage_online import latest_storage
from .timeseries import build_timeseries


WEB_ROOT = Path(__file__).resolve().parents[2] / "web"
COMMUNITY_COOKIE = "eea_community"
MAX_VOTE_BODY_BYTES = 4096
VOTE_RATE_LIMIT = 30
VOTE_RATE_WINDOW_SECONDS = 60


class VoteRateLimiter:
    def __init__(self, limit: int = VOTE_RATE_LIMIT, window_seconds: int = VOTE_RATE_WINDOW_SECONDS) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, identity: str, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        requests = self._requests[identity]
        while requests and requests[0] <= current - self.window_seconds:
            requests.popleft()
        if len(requests) >= self.limit:
            return False
        requests.append(current)
        return True


class AtlasHandler(BaseHTTPRequestHandler):
    db_path: Path
    community_store: CommunityStore
    vote_rate_limiter: VoteRateLimiter
    public_origin: str | None

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
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path != "/api/wallpaper-votes":
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            self._require_same_origin()
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                raise ValueError("vote request must use application/json")
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_VOTE_BODY_BYTES:
                raise ValueError("vote request must contain a small JSON body")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict) or set(payload) != {"wallpaper_id", "vote"}:
                raise ValueError("vote request must contain wallpaper_id and vote")
            wallpaper_id = payload["wallpaper_id"]
            vote = payload["vote"]
            if not isinstance(wallpaper_id, str) or not isinstance(vote, str):
                raise ValueError("vote request values must be strings")
            browser_id, created = self._browser_id(create=True)
            identity = browser_hash(browser_id)
            if not self.vote_rate_limiter.allow(identity):
                self._json({"error": "too many vote requests; please wait"}, HTTPStatus.TOO_MANY_REQUESTS)
                return
            state = self.community_store.cast_vote(wallpaper_id, identity, vote)
            headers = {"Set-Cookie": self._cookie_header(browser_id)} if created else None
            self._json({"wallpaper": state}, headers=headers)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def _api(self, path: str, query: dict[str, list[str]]) -> None:
        try:
            if path == "/api/wallpaper-votes":
                browser_id, _created = self._browser_id(create=False)
                payload = {"wallpapers": self.community_store.list_votes(browser_hash(browser_id) if browser_id else None)}
                self._json(payload)
                return
            if path == "/api/health":
                self._health()
                return
            year = int(query.get("year", ["2025"])[0])
            month_value = query.get("month", [""])[0]
            month = int(month_value) if month_value else None
            source = query.get("source", ["ember"])[0]
            if source != "ember":
                raise ValueError("source must be 'ember'")
            with read_database(self.db_path) as connection:
                if path == "/api/countries":
                    payload = [country.__dict__ for country in COUNTRIES.values()]
                elif path == "/api/metrics":
                    payload = metric_catalog()
                elif path == "/api/summary":
                    payload = aggregate_all(connection, year, month, source)
                elif path == "/api/country-profile":
                    payload = build_country_profile(
                        connection, query.get("country", [""])[0], year, month
                    )
                elif path == "/api/map-data":
                    payload = map_metric_dataset(
                        connection, query.get("metric", [""])[0], year, source
                    )
                elif path == "/api/compare":
                    codes = [code.upper() for code in query.get("countries", [""])[0].split(",") if code]
                    if not 2 <= len(codes) <= 4 or any(code not in COUNTRIES for code in codes):
                        raise ValueError("countries must contain 2 to 4 Atlas country codes")
                    payload = [aggregate_country(connection, code, year, month, source) for code in codes]
                elif path == "/api/timeseries":
                    codes = query.get("countries", [""])[0].split(",")
                    payload = build_timeseries(
                        connection,
                        query.get("metric", [""])[0],
                        codes,
                        query.get("start", [""])[0],
                        query.get("end", [""])[0],
                    )
                elif path == "/api/coverage":
                    payload = coverage_rows(connection, year)
                elif path == "/api/storage":
                    payload = latest_storage(connection)
                else:
                    self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                    return
            self._json(payload)
        except (ValueError, TypeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def _health(self) -> None:
        atlas_ok = False
        try:
            with read_database(self.db_path) as connection:
                connection.execute("SELECT 1 FROM period_observation LIMIT 1").fetchone()
            atlas_ok = True
        except Exception:
            atlas_ok = False
        community_ok = self.community_store.healthcheck()
        healthy = atlas_ok and community_ok
        self._json(
            {
                "status": "ok" if healthy else "unavailable",
                "atlas_database": "ok" if atlas_ok else "unavailable",
                "community_database": "ok" if community_ok else "unavailable",
            },
            HTTPStatus.OK if healthy else HTTPStatus.SERVICE_UNAVAILABLE,
        )

    def _browser_id(self, create: bool) -> tuple[str | None, bool]:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        value = cookie.get(COMMUNITY_COOKIE)
        if value and len(value.value) == 43:
            return value.value, False
        return (secrets.token_urlsafe(32), True) if create else (None, False)

    def _cookie_header(self, browser_id: str) -> str:
        cookie = SimpleCookie()
        cookie[COMMUNITY_COOKIE] = browser_id
        morsel = cookie[COMMUNITY_COOKIE]
        morsel["path"] = "/"
        morsel["httponly"] = True
        morsel["samesite"] = "Lax"
        if self.public_origin and self.public_origin.startswith("https://"):
            morsel["secure"] = True
        return morsel.OutputString()

    def _require_same_origin(self) -> None:
        origin = self.headers.get("Origin")
        if self.public_origin:
            if origin != self.public_origin:
                raise ValueError("vote requests must use the configured public origin")
            return
        if not origin:
            return
        expected = f"http://{self.headers.get('Host', '')}"
        if origin != expected:
            raise ValueError("cross-origin vote requests are not allowed")

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "camera=(), geolocation=(), microphone=()")

    def log_message(self, format: str, *args: object) -> None:
        print(f"[http] {format % args}")


def create_server(
    db_path: Path,
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    community_path: Path | None = None,
    public_origin: str | None = None,
    require_existing_db: bool = False,
) -> ThreadingHTTPServer:
    db_path = Path(db_path)
    if require_existing_db:
        validate_existing_atlas_database(db_path)
    elif not db_path.exists():
        with database(db_path):
            pass
    resolved_community_path = Path(community_path) if community_path is not None else Path(
        os.environ.get("EEA_COMMUNITY_DB", DEFAULT_COMMUNITY_DB)
    )
    community_store = CommunityStore(resolved_community_path)
    community_store.initialize()
    handler = type("ConfiguredAtlasHandler", (AtlasHandler,), {
        "db_path": db_path,
        "community_store": community_store,
        "vote_rate_limiter": VoteRateLimiter(),
        "public_origin": parse_public_origin(public_origin),
    })
    return ThreadingHTTPServer((host, port), handler)


def serve(
    db_path: Path,
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    community_path: Path | None = None,
    public_origin: str | None = None,
    require_existing_db: bool = False,
) -> None:
    server = create_server(
        db_path,
        host,
        port,
        community_path=community_path,
        public_origin=public_origin,
        require_existing_db=require_existing_db,
    )
    print(f"European Electricity Atlas: http://{host}:{port}")
    print(f"SQLite: {db_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

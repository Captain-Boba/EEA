from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import API_BASE_URL


class ApiError(RuntimeError):
    pass


class EnergyChartsClient:
    def __init__(self, connection: sqlite3.Connection, base_url: str = API_BASE_URL, timeout: int = 90):
        self.connection = connection
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(
        self,
        endpoint: str,
        target_name: str,
        target: str,
        start_date: str = "",
        end_date: str = "",
        extra: dict[str, str] | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        endpoint = endpoint.strip("/")
        if not refresh:
            row = self.connection.execute(
                """SELECT response_json FROM api_cache
                   WHERE endpoint=? AND target=? AND start_date=? AND end_date=?""",
                (endpoint, target, start_date, end_date),
            ).fetchone()
            if row:
                return json.loads(row["response_json"])
            if start_date and end_date:
                row = self.connection.execute(
                    """SELECT response_json FROM api_cache
                       WHERE endpoint=? AND target=? AND start_date<>'' AND end_date<>''
                         AND start_date<=? AND end_date>=?
                       ORDER BY julianday(end_date)-julianday(start_date) ASC
                       LIMIT 1""",
                    (endpoint, target, start_date, end_date),
                ).fetchone()
                if row:
                    payload = json.loads(row["response_json"])
                    selected = [
                        record for record in payload.get("data", [])
                        if start_date <= str(record.get("timestamp", ""))[:10] <= end_date
                    ]
                    payload["data"] = selected
                    if selected:
                        payload["available_from"] = selected[0]["timestamp"]
                        payload["available_until"] = selected[-1]["timestamp"]
                    return payload

        params = {target_name: target}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
        if extra:
            params.update(extra)
        url = f"{self.base_url}/{endpoint}?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": "European-Electricity-Atlas/0.1"})
        payload_bytes: bytes | None = None
        status = 0
        for attempt in range(5):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    payload_bytes = response.read()
                    status = response.status
                    break
            except HTTPError as exc:
                if exc.code == 429 and attempt < 4:
                    retry_after = int(exc.headers.get("Retry-After", "0") or 0)
                    time.sleep(max(retry_after, 2 ** attempt))
                    continue
                if exc.code == 404:
                    payload = {"data": [], "coverage_status": "not_available"}
                    raw = json.dumps(payload, separators=(",", ":"))
                    self.connection.execute(
                        """INSERT INTO api_cache
                           (endpoint,target,start_date,end_date,request_url,fetched_at,status_code,sha256,response_json)
                           VALUES (?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(endpoint,target,start_date,end_date) DO UPDATE SET
                             request_url=excluded.request_url,fetched_at=excluded.fetched_at,
                             status_code=excluded.status_code,sha256=excluded.sha256,
                             response_json=excluded.response_json""",
                        (
                            endpoint,
                            target,
                            start_date,
                            end_date,
                            url,
                            datetime.now(UTC).isoformat(),
                            404,
                            hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                            raw,
                        ),
                    )
                    self.connection.commit()
                    return payload
                detail = exc.read().decode("utf-8", errors="replace")
                raise ApiError(f"Energy-Charts {endpoint} returned HTTP {exc.code}: {detail}") from exc
            except URLError as exc:
                raise ApiError(f"Energy-Charts {endpoint} could not be reached: {exc.reason}") from exc
        if payload_bytes is None:
            raise ApiError(f"Energy-Charts {endpoint} rate limit persisted after retries")

        try:
            payload = json.loads(payload_bytes)
        except json.JSONDecodeError as exc:
            raise ApiError(f"Energy-Charts {endpoint} returned invalid JSON") from exc
        raw = payload_bytes.decode("utf-8")
        self.connection.execute(
            """INSERT INTO api_cache
               (endpoint,target,start_date,end_date,request_url,fetched_at,status_code,sha256,response_json)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(endpoint,target,start_date,end_date) DO UPDATE SET
                 request_url=excluded.request_url,
                 fetched_at=excluded.fetched_at,
                 status_code=excluded.status_code,
                 sha256=excluded.sha256,
                 response_json=excluded.response_json""",
            (
                endpoint,
                target,
                start_date,
                end_date,
                url,
                datetime.now(UTC).isoformat(),
                status,
                hashlib.sha256(payload_bytes).hexdigest(),
                raw,
            ),
        )
        self.connection.commit()
        return payload

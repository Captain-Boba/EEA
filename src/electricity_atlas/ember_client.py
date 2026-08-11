from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import EMBER_API_BASE_URL


class EmberKeyError(RuntimeError):
    pass


class EmberApiError(RuntimeError):
    pass


def load_ember_api_key(
    key_file: Path | str = Path("EMBER_API_KEY.txt"),
    environ: Mapping[str, str] | None = None,
) -> str:
    environment = os.environ if environ is None else environ
    if "EMBER_API_KEY" in environment:
        value = environment["EMBER_API_KEY"].strip()
        if not value:
            raise EmberKeyError("EMBER_API_KEY is set but empty")
        return value
    path = Path(key_file)
    if not path.is_file():
        raise EmberKeyError("Ember API key is missing; set EMBER_API_KEY or create EMBER_API_KEY.txt")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise EmberKeyError("EMBER_API_KEY.txt is empty")
    return value


def _redact_text(value: str, secret: str) -> str:
    return value.replace(secret, "REDACTED") if secret else value


def _redact_payload(value: Any, secret: str) -> Any:
    if isinstance(value, dict):
        return {
            key: "REDACTED" if str(key).lower() == "api_key" else _redact_payload(item, secret)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_payload(item, secret) for item in value]
    if isinstance(value, str):
        return _redact_text(value, secret)
    return value


class EmberClient:
    def __init__(
        self,
        connection: sqlite3.Connection,
        base_url: str = EMBER_API_BASE_URL,
        timeout: int = 90,
        key_file: Path | str = Path("EMBER_API_KEY.txt"),
    ):
        self.connection = connection
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._api_key = load_ember_api_key(key_file)

    def get(
        self,
        endpoint: str,
        entity_code: str,
        start_date: str,
        end_date: str,
        extra: dict[str, str] | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        params = {"entity_code": entity_code, "start_date": start_date, "end_date": end_date}
        if extra:
            params.update(extra)
        cache_target = entity_code
        if extra:
            cache_target += "|" + "&".join(f"{key}={extra[key]}" for key in sorted(extra))
        legacy_target = (
            entity_code if extra == {"is_aggregate_series": "false"} else None
        )
        return self._request(
            endpoint,
            cache_target,
            start_date,
            end_date,
            params,
            refresh,
            legacy_target=legacy_target,
        )

    def options(
        self,
        dataset: str,
        temporal_resolution: str,
        filter_name: str,
        refresh: bool = False,
    ) -> dict[str, Any]:
        endpoint = f"options/{dataset.strip('/')}/{temporal_resolution.strip('/')}/{filter_name.strip('/')}"
        target = f"{dataset}:{temporal_resolution}:{filter_name}"
        return self._request(endpoint, target, "", "", {}, refresh)

    def _request(
        self,
        endpoint: str,
        target: str,
        start_date: str,
        end_date: str,
        params: dict[str, str],
        refresh: bool,
        legacy_target: str | None = None,
    ) -> dict[str, Any]:
        normalized_endpoint = endpoint.strip("/")
        cache_endpoint = f"ember/{normalized_endpoint}"
        if not refresh:
            for candidate_target in (target, legacy_target):
                if candidate_target is None:
                    continue
                row = self.connection.execute(
                    """SELECT response_json FROM api_cache
                       WHERE endpoint=? AND target=? AND start_date=? AND end_date=?""",
                    (cache_endpoint, candidate_target, start_date, end_date),
                ).fetchone()
                if row:
                    payload = json.loads(row["response_json"])
                    if candidate_target == target or self._is_non_aggregate_generation(payload):
                        return payload
                covering = self.connection.execute(
                    """SELECT response_json FROM api_cache
                       WHERE endpoint=? AND target=? AND start_date<=? AND end_date>=?
                       ORDER BY start_date DESC, end_date ASC
                       LIMIT 1""",
                    (cache_endpoint, candidate_target, start_date, end_date),
                ).fetchone()
                if covering:
                    payload = json.loads(covering["response_json"])
                    if candidate_target == target or self._is_non_aggregate_generation(payload):
                        return self._slice_cached_payload(
                            payload, normalized_endpoint, start_date, end_date
                        )

        request_params = dict(params)
        request_params["api_key"] = self._api_key
        actual_url = f"{self.base_url}/{normalized_endpoint}?{urlencode(request_params)}"
        redacted_params = dict(params)
        redacted_params["api_key"] = "REDACTED"
        redacted_url = f"{self.base_url}/{normalized_endpoint}?{urlencode(redacted_params)}"
        request = Request(actual_url, headers={"User-Agent": "European-Electricity-Atlas/0.1"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload_bytes = response.read()
                status = response.status
        except HTTPError as exc:
            detail = _redact_text(exc.read().decode("utf-8", errors="replace"), self._api_key)
            raise EmberApiError(f"Ember {normalized_endpoint} returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            reason = _redact_text(str(exc.reason), self._api_key)
            raise EmberApiError(f"Ember {normalized_endpoint} could not be reached: {reason}") from exc

        try:
            decoded = json.loads(payload_bytes)
        except json.JSONDecodeError as exc:
            raise EmberApiError(f"Ember {normalized_endpoint} returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise EmberApiError(f"Ember {normalized_endpoint} returned a non-object payload")
        payload = _redact_payload(decoded, self._api_key)
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
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
                cache_endpoint,
                target,
                start_date,
                end_date,
                redacted_url,
                datetime.now(UTC).isoformat(),
                status,
                hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                raw,
            ),
        )
        self.connection.commit()
        return payload

    @staticmethod
    def _is_non_aggregate_generation(payload: dict[str, Any]) -> bool:
        rows = payload.get("data")
        return isinstance(rows, list) and all(
            isinstance(row, dict) and row.get("is_aggregate_series") is False
            for row in rows
        )

    @staticmethod
    def _slice_cached_payload(
        payload: dict[str, Any], endpoint: str, start_date: str, end_date: str
    ) -> dict[str, Any]:
        rows = payload.get("data")
        if not isinstance(rows, list) or not start_date or not end_date:
            return payload
        if endpoint.endswith("/monthly"):
            payload["data"] = [
                row
                for row in rows
                if isinstance(row, dict)
                and start_date <= str(row.get("date", ""))[:7] < end_date
            ]
        elif endpoint.endswith("/yearly"):
            payload["data"] = [
                row
                for row in rows
                if isinstance(row, dict)
                and start_date <= str(row.get("date", ""))[:4] <= end_date
            ]
        return payload

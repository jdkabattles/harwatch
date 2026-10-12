"""Turn a HAR into a stable contract. Secret values are never kept."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

SECRET_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key", "x-auth-token"}
SECRET_QUERY = {"token", "access_token", "api_key", "apikey", "key", "secret"}


def load(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if "log" not in data or "entries" not in data["log"]:
        raise ValueError("Not a HAR: missing log.entries")
    return data


def contract(har: dict[str, Any]) -> dict[str, Any]:
    endpoints: dict[str, Any] = {}
    for entry in har["log"]["entries"]:
        req = entry.get("request") or {}
        res = entry.get("response") or {}
        url = req.get("url") or ""
        if not url.startswith(("http://", "https://")):
            continue
        parsed = urlparse(url)
        method = (req.get("method") or "GET").upper()
        key = f"{method} {parsed.path or '/'}"
        query = sorted(
            name for name, _ in parse_qsl(parsed.query) if name.lower() not in SECRET_QUERY
        )
        endpoints[key] = _merge(endpoints.get(key), {
            "host": parsed.netloc,
            "query": query,
            "status": res.get("status") or 0,
            "response": _shape(_json_or_none((res.get("content") or {}).get("text"))),
            "request": _shape(_json_or_none((req.get("postData") or {}).get("text"))),
        })
    if not endpoints:
        raise ValueError("No HTTP calls in HAR")
    return {"version": 1, "endpoints": endpoints}


def diff(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    breaks: list[str] = []
    old_eps = old.get("endpoints") or {}
    new_eps = new.get("endpoints") or {}
    for key, prev in old_eps.items():
        if key not in new_eps:
            breaks.append(f"removed {key}")
            continue
        cur = new_eps[key]
        missing = _missing_fields(prev.get("response"), cur.get("response"))
        for field in missing:
            breaks.append(f"removed field {key} response.{field}")
        if prev.get("status") and cur.get("status") and prev["status"] != cur["status"]:
            breaks.append(f"status {key} {prev['status']} -> {cur['status']}")
    return breaks


def _json_or_none(text: str | None) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(value[0])] if value else []
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if value is None:
        return "null"
    return "string"


def _merge(prev: dict[str, Any] | None, cur: dict[str, Any]) -> dict[str, Any]:
    if prev is None:
        return cur
    return {
        "host": prev["host"] or cur["host"],
        "query": sorted(set(prev["query"]) | set(cur["query"])),
        "status": prev["status"] or cur["status"],
        "response": _union(prev["response"], cur["response"]),
        "request": _union(prev["request"], cur["request"]),
    }


def _union(old: Any, new: Any) -> Any:
    if isinstance(old, dict) and isinstance(new, dict):
        keys = set(old) | set(new)
        return {key: _union(old.get(key), new.get(key)) for key in sorted(keys)}
    if isinstance(old, list) and isinstance(new, list):
        if not old:
            return new
        if not new:
            return old
        return [_union(old[0], new[0])]
    return old if old is not None else new


def _missing_fields(old: Any, new: Any, prefix: str = "") -> list[str]:
    if isinstance(old, dict):
        if not isinstance(new, dict):
            return [prefix or "$"]
        missing = []
        for key, shape in old.items():
            path = f"{prefix}.{key}" if prefix else key
            if key not in new:
                missing.append(path)
            else:
                missing.extend(_missing_fields(shape, new[key], path))
        return missing
    if isinstance(old, list):
        if not isinstance(new, list) or not new:
            return [prefix or "$"]
        return _missing_fields(old[0], new[0], prefix)
    return []

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _load_raw_response(raw_response: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(raw_response, dict):
        return raw_response
    if isinstance(raw_response, str):
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError(f"raw_response is not valid JSON: {exc.msg}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("raw_response JSON must decode to an object")
        return parsed
    raise ValueError("raw_response must be a dict or JSON string")


def _require_string(item: dict[str, Any], field_name: str, index: int) -> str:
    value = item.get(field_name)
    if value is None:
        raise ValueError(f"items[{index}] missing required field '{field_name}'")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"items[{index}] field '{field_name}' must be a non-empty string")
    return value


def _normalize_updated_at(value: Any, index: int) -> str:
    if value is None:
        raise ValueError(f"items[{index}] missing required field 'updated_at'")
    if isinstance(value, bool):
        raise ValueError(f"items[{index}] field 'updated_at' must be an epoch number or ISO string")
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, tz=UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, str) and value.strip():
        text = value.strip()
        normalized = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError(f"items[{index}] field 'updated_at' is not a valid ISO timestamp: {text}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
    raise ValueError(f"items[{index}] field 'updated_at' must be an epoch number or ISO string")


def convert_mcp_search_response(raw_response: dict[str, Any] | str) -> list[dict[str, str]]:
    payload = _load_raw_response(raw_response)
    items = payload.get("items")
    if items is None:
        raise ValueError("raw_response missing required field 'items'")
    if not isinstance(items, list):
        raise ValueError("raw_response field 'items' must be a list")

    manifest: list[dict[str, str]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"items[{index}] must be an object")
        manifest.append(
            {
                "designId": _require_string(item, "id", index).strip(),
                "title": _require_string(item, "title", index).strip(),
                "updatedAt": _normalize_updated_at(item.get("updated_at"), index),
            }
        )
    return manifest


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) != 1:
        print("usage: python3 mcp_to_manifest.py <raw_response.json>", file=sys.stderr)
        return 2

    raw_path = Path(argv[0])
    manifest = convert_mcp_search_response(raw_path.read_text(encoding="utf-8"))
    json.dump(manifest, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

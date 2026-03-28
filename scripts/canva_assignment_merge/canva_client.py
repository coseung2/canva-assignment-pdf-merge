from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from .models import SearchDesignRecord


class CanvaClient(Protocol):
    def search_designs(self, query: str) -> list[SearchDesignRecord]:
        ...

    def export_design_to_pdf(self, design_id: str) -> bytes:
        ...


def _parse_updated_at(raw: str | None) -> datetime:
    if not raw:
        return datetime.fromtimestamp(0)
    normalized = raw.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def load_json_file(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


@dataclass(slots=True)
class ManifestCanvaClient:
    search_results: list[dict[str, Any]]
    export_map: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_files(
        cls,
        search_results_file: str | Path,
        export_map_file: str | Path | None = None,
    ) -> "ManifestCanvaClient":
        search_results = load_json_file(search_results_file)
        export_map = load_json_file(export_map_file) if export_map_file else {}
        return cls(search_results=search_results, export_map=export_map)

    def search_designs(self, query: str) -> list[SearchDesignRecord]:
        query = query.strip()
        records: list[SearchDesignRecord] = []
        for item in self.search_results:
            title = str(item.get("title", ""))
            if query and query not in title:
                continue
            design_id = str(item.get("designId") or item.get("design_id") or "")
            if not design_id:
                continue
            metadata = {
                key: value
                for key, value in item.items()
                if key not in {"designId", "design_id", "title", "updatedAt", "updated_at"}
            }
            records.append(
                SearchDesignRecord(
                    design_id=design_id,
                    title=title,
                    updated_at=_parse_updated_at(item.get("updatedAt") or item.get("updated_at")),
                    metadata=metadata,
                )
            )
        return records

    def export_design_to_pdf(self, design_id: str) -> bytes:
        if design_id not in self.export_map:
            raise FileNotFoundError(f"missing export map for design_id={design_id}")

        export_entry = self.export_map[design_id]
        if isinstance(export_entry, dict) and "path" in export_entry:
            return Path(export_entry["path"]).read_bytes()
        if isinstance(export_entry, dict) and "base64" in export_entry:
            return base64.b64decode(export_entry["base64"])
        if isinstance(export_entry, str):
            return Path(export_entry).read_bytes()
        raise ValueError(f"unsupported export entry for design_id={design_id}")


class BackendCanvaClient:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def search_designs(self, query: str) -> list[SearchDesignRecord]:
        raise NotImplementedError(
            "Implement search_designs() with your Canva backend or connector. "
            "Keep the method signature stable so the collector remains deterministic."
        )

    def export_design_to_pdf(self, design_id: str) -> bytes:
        raise NotImplementedError(
            "Implement export_design_to_pdf() with your Canva backend or connector. "
            "Return raw PDF bytes for the selected design."
        )

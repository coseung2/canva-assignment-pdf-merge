from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class SearchDesignRecord:
    design_id: str
    title: str
    updated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedTitle:
    status: str
    assignment_name: str
    student_number: int
    student_name: str
    original_title: str


@dataclass(slots=True)
class ValidationIssue:
    design_id: str
    title: str
    reason: str
    detail: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SelectedSubmission:
    design_id: str
    title: str
    updated_at: datetime
    student_number: int
    student_name: str
    assignment_name: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["updated_at"] = self.updated_at.isoformat()
        return payload


@dataclass(slots=True)
class DuplicateResolution:
    student_number: int
    kept_design_id: str
    kept_title: str
    replaced_design_id: str
    replaced_title: str
    resolution: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExportResult:
    design_id: str
    student_number: int
    student_name: str
    title: str
    pdf_path: str | None = None
    status: str = "success"
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

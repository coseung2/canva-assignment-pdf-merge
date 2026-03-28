from __future__ import annotations

import re

from .models import ParsedTitle, SearchDesignRecord, ValidationIssue

STRICT_PATTERN = re.compile(r"^완료\s*-\s*(.+?)\s*-\s*(\d+)\s*-\s*(.+)$")
RELAXED_PATTERN = re.compile(r"^완료\s*-\s*(.+?)\s*-\s*(\d+)\s*-\s*(.+)$")


def parse_title(
    record: SearchDesignRecord,
    expected_assignment_name: str,
    strict_mode: bool = True,
) -> tuple[ParsedTitle | None, ValidationIssue | None]:
    title = record.title.strip()
    if not title.startswith("완료"):
        return None, ValidationIssue(
            design_id=record.design_id,
            title=record.title,
            reason="title_format_invalid",
            detail="title must start with 완료",
            updated_at=record.updated_at.isoformat(),
        )

    pattern = STRICT_PATTERN if strict_mode else RELAXED_PATTERN
    match = pattern.fullmatch(title)
    if not match:
        detail = "title did not match expected pattern"
        return None, ValidationIssue(
            design_id=record.design_id,
            title=record.title,
            reason="title_format_invalid",
            detail=detail,
            updated_at=record.updated_at.isoformat(),
        )

    assignment_name = match.group(1).strip()
    student_number_raw = match.group(2).strip()
    student_name = match.group(3).strip()

    if assignment_name != expected_assignment_name.strip():
        return None, ValidationIssue(
            design_id=record.design_id,
            title=record.title,
            reason="assignment_name_mismatch",
            detail=f"expected '{expected_assignment_name.strip()}', got '{assignment_name}'",
            updated_at=record.updated_at.isoformat(),
        )

    if not student_number_raw.isdigit():
        return None, ValidationIssue(
            design_id=record.design_id,
            title=record.title,
            reason="invalid_student_number",
            detail=f"studentNumber '{student_number_raw}' is not numeric",
            updated_at=record.updated_at.isoformat(),
        )

    if not student_name:
        return None, ValidationIssue(
            design_id=record.design_id,
            title=record.title,
            reason="missing_student_name",
            detail="studentName is empty",
            updated_at=record.updated_at.isoformat(),
        )

    return (
        ParsedTitle(
            status="완료",
            assignment_name=assignment_name,
            student_number=int(student_number_raw),
            student_name=student_name,
            original_title=record.title,
        ),
        None,
    )

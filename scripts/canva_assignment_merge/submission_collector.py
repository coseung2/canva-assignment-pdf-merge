from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .canva_client import CanvaClient
from .models import DuplicateResolution, SearchDesignRecord, SelectedSubmission, ValidationIssue
from .title_parser import parse_title


@dataclass(slots=True)
class CollectionResult:
    search_queries: list[str]
    total_search_hits: int
    total_parsed_valid: int
    selected_submissions: list[SelectedSubmission]
    invalid_titles: list[ValidationIssue]
    assignment_mismatches: list[ValidationIssue]
    skipped_designs: list[ValidationIssue]
    duplicate_resolutions: list[DuplicateResolution]


def _dedupe_records(records: Iterable[SearchDesignRecord]) -> list[SearchDesignRecord]:
    by_design_id: dict[str, SearchDesignRecord] = {}
    for record in records:
        current = by_design_id.get(record.design_id)
        if current is None or record.updated_at > current.updated_at:
            by_design_id[record.design_id] = record
    return list(by_design_id.values())


def collect_submissions(
    client: CanvaClient,
    assignment_name: str,
    strict_mode: bool = True,
) -> CollectionResult:
    primary_query = f"완료 - {assignment_name.strip()} -"
    fallback_query = assignment_name.strip()

    search_queries = [primary_query]
    primary_hits = client.search_designs(primary_query)
    if not primary_hits:
        search_queries.append(fallback_query)
        records = client.search_designs(fallback_query)
    else:
        fallback_hits = client.search_designs(fallback_query)
        search_queries.append(fallback_query)
        records = primary_hits + fallback_hits

    deduped_hits = _dedupe_records(records)
    invalid_titles: list[ValidationIssue] = []
    assignment_mismatches: list[ValidationIssue] = []
    duplicate_resolutions: list[DuplicateResolution] = []
    selected_by_student: dict[int, SelectedSubmission] = {}

    total_parsed_valid = 0

    for record in deduped_hits:
        parsed, issue = parse_title(record, expected_assignment_name=assignment_name, strict_mode=strict_mode)
        if issue:
            if issue.reason == "assignment_name_mismatch":
                assignment_mismatches.append(issue)
            else:
                invalid_titles.append(issue)
            continue

        total_parsed_valid += 1
        candidate = SelectedSubmission(
            design_id=record.design_id,
            title=record.title,
            updated_at=record.updated_at,
            student_number=parsed.student_number,
            student_name=parsed.student_name,
            assignment_name=parsed.assignment_name,
            metadata=record.metadata,
        )
        existing = selected_by_student.get(candidate.student_number)
        if existing is None:
            selected_by_student[candidate.student_number] = candidate
            continue

        keep, replace = (candidate, existing) if candidate.updated_at >= existing.updated_at else (existing, candidate)
        selected_by_student[candidate.student_number] = keep
        detail = f"kept latest updatedAt; names: '{keep.student_name}' vs '{replace.student_name}'"
        duplicate_resolutions.append(
            DuplicateResolution(
                student_number=keep.student_number,
                kept_design_id=keep.design_id,
                kept_title=keep.title,
                replaced_design_id=replace.design_id,
                replaced_title=replace.title,
                resolution="latest_updated_at",
                detail=detail,
            )
        )

    selected_submissions = sorted(selected_by_student.values(), key=lambda item: item.student_number)
    skipped_designs: list[ValidationIssue] = [
        ValidationIssue(
            design_id=entry.replaced_design_id,
            title=entry.replaced_title,
            reason="duplicate_replaced_by_latest",
            detail=entry.detail,
        )
        for entry in duplicate_resolutions
    ]

    return CollectionResult(
        search_queries=search_queries,
        total_search_hits=len(deduped_hits),
        total_parsed_valid=total_parsed_valid,
        selected_submissions=selected_submissions,
        invalid_titles=invalid_titles,
        assignment_mismatches=assignment_mismatches,
        skipped_designs=skipped_designs,
        duplicate_resolutions=duplicate_resolutions,
    )

from __future__ import annotations

from .models import ExportResult
from .submission_collector import CollectionResult


def build_report(
    assignment_name: str,
    output_file_name: str,
    strict_mode: bool,
    collection: CollectionResult,
    export_results: list[ExportResult],
) -> dict:
    selected_students = [
        {
            "studentNumber": item.student_number,
            "studentName": item.student_name,
            "designId": item.design_id,
            "title": item.title,
        }
        for item in collection.selected_submissions
    ]
    successful_exports = [result for result in export_results if result.status == "success"]
    export_failures = [result for result in export_results if result.status != "success"]

    return {
        "assignmentName": assignment_name,
        "outputFileName": output_file_name,
        "strictMode": strict_mode,
        "summary": {
            "totalSearchHits": collection.total_search_hits,
            "totalParsedValid": collection.total_parsed_valid,
            "totalExported": len(successful_exports),
            "duplicatesFound": len(collection.duplicate_resolutions),
            "invalidTitles": len(collection.invalid_titles),
            "skippedDesigns": len(collection.skipped_designs) + len(collection.assignment_mismatches) + len(export_failures),
            "selectedStudents": selected_students,
        },
        "searchQueries": collection.search_queries,
        "invalidTitleList": [issue.to_dict() for issue in collection.invalid_titles],
        "assignmentMismatchList": [issue.to_dict() for issue in collection.assignment_mismatches],
        "duplicatesResolved": [entry.to_dict() for entry in collection.duplicate_resolutions],
        "exportFailures": [result.to_dict() for result in export_failures],
        "skippedDesigns": [issue.to_dict() for issue in collection.skipped_designs],
        "finalSelectedOrder": [
            {
                "studentNumber": item.student_number,
                "studentName": item.student_name,
                "designId": item.design_id,
                "title": item.title,
            }
            for item in collection.selected_submissions
        ],
    }

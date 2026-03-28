from __future__ import annotations

import json
import logging
from pathlib import Path

from .canva_client import BackendCanvaClient, CanvaClient, ManifestCanvaClient
from .models import ExportResult
from .pdf_merger import merge_pdf_buffers
from .report_builder import build_report
from .submission_collector import collect_submissions

LOGGER = logging.getLogger("canva_assignment_merge")


def run_assignment_merge(
    assignment_name: str,
    output_dir: str | Path,
    output_file_name: str | None = None,
    strict_mode: bool = True,
    client: CanvaClient | None = None,
    search_results_file: str | Path | None = None,
    export_map_file: str | Path | None = None,
    backend_config_file: str | Path | None = None,
) -> dict:
    assignment_name = assignment_name.strip()
    output_file_name = output_file_name or f"{assignment_name}_완료본_병합.pdf"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if client is None:
        if search_results_file:
            client = ManifestCanvaClient.from_files(search_results_file, export_map_file)
        else:
            backend_config = {}
            if backend_config_file:
                backend_config = json.loads(Path(backend_config_file).read_text(encoding="utf-8"))
            client = BackendCanvaClient(config=backend_config)

    collection = collect_submissions(client=client, assignment_name=assignment_name, strict_mode=strict_mode)
    LOGGER.info("search queries: %s", ", ".join(collection.search_queries))
    LOGGER.info("search hits: %s", collection.total_search_hits)
    LOGGER.info("parse valid=%s invalid=%s mismatches=%s", collection.total_parsed_valid, len(collection.invalid_titles), len(collection.assignment_mismatches))
    LOGGER.info("duplicates resolved: %s", len(collection.duplicate_resolutions))

    if not collection.selected_submissions:
        raise RuntimeError(f"no valid completed submissions found for assignment '{assignment_name}'")

    export_results: list[ExportResult] = []
    exported_buffers: list[bytes] = []

    for index, submission in enumerate(collection.selected_submissions, start=1):
        LOGGER.info(
            "exporting %s/%s student=%s design_id=%s",
            index,
            len(collection.selected_submissions),
            submission.student_number,
            submission.design_id,
        )
        try:
            pdf_bytes = client.export_design_to_pdf(submission.design_id)
            pdf_path = output_dir / f"{submission.student_number:03d}_{submission.student_name}.pdf"
            pdf_path.write_bytes(pdf_bytes)
            exported_buffers.append(pdf_bytes)
            export_results.append(
                ExportResult(
                    design_id=submission.design_id,
                    student_number=submission.student_number,
                    student_name=submission.student_name,
                    title=submission.title,
                    pdf_path=str(pdf_path),
                )
            )
        except Exception as exc:  # pragma: no cover - exercised in tests via broad failure path
            LOGGER.error("export failed for design_id=%s: %s", submission.design_id, exc)
            export_results.append(
                ExportResult(
                    design_id=submission.design_id,
                    student_number=submission.student_number,
                    student_name=submission.student_name,
                    title=submission.title,
                    status="failed",
                    reason="export_failed",
                )
            )
            if strict_mode:
                raise RuntimeError(f"export failed for design_id={submission.design_id}") from exc

    if not exported_buffers:
        raise RuntimeError("no PDFs exported successfully")

    merged_pdf = merge_pdf_buffers(exported_buffers)
    merged_pdf_path = output_dir / output_file_name
    merged_pdf_path.write_bytes(merged_pdf)
    LOGGER.info("merge completed: %s", merged_pdf_path)

    report = build_report(
        assignment_name=assignment_name,
        output_file_name=output_file_name,
        strict_mode=strict_mode,
        collection=collection,
        export_results=export_results,
    )
    report["mergedPdfPath"] = str(merged_pdf_path)
    report_path = output_dir / f"{merged_pdf_path.stem}_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["reportPath"] = str(report_path)
    return report

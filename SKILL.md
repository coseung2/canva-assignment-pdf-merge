---
name: canva-assignment-pdf-merge
description: Collect completed Canva student submissions by strict title pattern, validate and deduplicate them by student number, export each selected design as PDF through a swappable adapter, then merge the PDFs and emit a validation report. Use when a user asks to merge completed Canva assignments such as "여행지 과제 완료본 병합해줘" without relying on Canva assignment-tab status.
---

# Canva Assignment PDF Merge

Use this skill when the user wants a single PDF compiled from completed Canva assignments and the source of truth is the design title:

`완료 - {assignmentName} - {studentNumber} - {studentName}`

Do not rely on Canva assignment tabs or submission status. Only the title convention counts.

## Inputs

- Required: `assignmentName`
- Optional: `outputFileName`
- Optional: `strictMode` (default `true`)

## Workflow

1. Search Canva designs with the primary query `완료 - {assignmentName} -`.
2. If needed, run a broader fallback search, then locally validate every returned title with the parser.
3. Keep only titles that parse cleanly and whose parsed assignment name matches exactly after trimming.
4. Deduplicate by `studentNumber`, keeping the most recently updated design and reporting the conflict.
5. Export the selected designs as PDFs through the configured Canva adapter.
6. Merge PDFs in ascending `studentNumber` order.
7. Return the merged PDF path plus the JSON validation report.

## Deterministic Rules

- `strictMode=true` still uses `-` as the required separator, but does not require spaces around it.
- `strictMode=false` relaxes separator spacing, but still requires:
  - title starts with `완료`
  - numeric `studentNumber`
  - non-empty `studentName`
  - exact `assignmentName` match after trim
- Never trust raw search hits without local parsing.
- Export failures fail the run in strict mode.
- In non-strict mode, continue if at least one PDF exports successfully.

## Files

- Core package: `scripts/canva_assignment_merge/`
- CLI entrypoint: `scripts/merge_completed_assignments.py`
- Tests: `tests/test_assignment_merge.py`
- Example report and notes: `references/`

## Usage

Install dependency first:

```bash
python3 -m pip install pypdf
```

End-to-end quick start: run Canva MCP design search with the query `완료 - 여행지 -`, save the raw JSON response, convert it to manifest format with `python3 canva-assignment-pdf-merge/scripts/canva_assignment_merge/mcp_to_manifest.py /path/to/raw_response.json > /path/to/search_results.json`, prepare an export map JSON keyed by `designId`, then run `python3 canva-assignment-pdf-merge/scripts/merge_completed_assignments.py --assignment-name "여행지" --search-results-file /path/to/search_results.json --export-map-file /path/to/export_map.json --output-dir /path/to/output` to produce the merged PDF and validation report.

Manifest mode is the lowest-friction path for current Canva MCP limitations:

1. Gather Canva search results into JSON with records containing:
   - `designId`
   - `title`
   - `updatedAt`
   - optional edit/view/export metadata
2. Export PDFs through your connected backend or connector and write an export map JSON keyed by `designId`.
3. Run:

```bash
python3 canva-assignment-pdf-merge/scripts/merge_completed_assignments.py \
  --assignment-name "여행지" \
  --search-results-file /path/to/search_results.json \
  --export-map-file /path/to/export_map.json \
  --output-dir /path/to/output
```

## Adapter Notes

- `ManifestCanvaClient` is fully implemented for deterministic local runs and tests.
- `BackendCanvaClient` is the swappable integration point for a real Canva export/search backend.
- If a future Canva connector exposes export directly, wire that logic into `canva_client.py` instead of changing the collector, merger, or report code.

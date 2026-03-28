# Implementation Notes

## Plan

1. Search Canva designs with a narrow title-based query, then a broader fallback.
2. Parse every returned title locally with deterministic validation.
3. Filter exact assignment-name matches and reject malformed titles.
4. Deduplicate by student number using latest `updatedAt`.
5. Export selected designs through a swappable adapter.
6. Merge exported PDFs in ascending student-number order.
7. Emit a JSON validation report alongside the merged PDF.

## Recommended Stack

- Runtime: Python 3.12
- PDF merge: `pypdf`
- Tests: `unittest`
- Integration boundary: `CanvaClient` protocol in `scripts/canva_assignment_merge/canva_client.py`

## Error Handling Strategy

- Malformed titles are excluded and reported.
- Assignment mismatches are excluded and reported separately.
- Duplicate student numbers are resolved by latest `updatedAt` and recorded.
- `strictMode=true`: first export failure fails the run.
- `strictMode=false`: export failures are reported and the run continues if at least one PDF succeeds.
- No valid submissions or zero successful exports raise hard errors.

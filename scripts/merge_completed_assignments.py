#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging

from canva_assignment_merge import run_assignment_merge


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge completed Canva assignment PDFs by title pattern.")
    parser.add_argument("--assignment-name", required=True)
    parser.add_argument("--output-file-name")
    parser.add_argument("--output-dir", default="./out")
    parser.add_argument("--strict-mode", type=parse_bool, default=True)
    parser.add_argument("--search-results-file")
    parser.add_argument("--export-map-file")
    parser.add_argument("--backend-config-file")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    report = run_assignment_merge(
        assignment_name=args.assignment_name,
        output_dir=args.output_dir,
        output_file_name=args.output_file_name,
        strict_mode=args.strict_mode,
        search_results_file=args.search_results_file,
        export_map_file=args.export_map_file,
        backend_config_file=args.backend_config_file,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

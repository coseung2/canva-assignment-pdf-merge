from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from canva_assignment_merge.canva_client import ManifestCanvaClient
from canva_assignment_merge.main import run_assignment_merge
from canva_assignment_merge.models import SearchDesignRecord
from canva_assignment_merge.title_parser import parse_title


def build_pdf_bytes(label: str) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/Title": label})
    temp_path = Path(tempfile.gettempdir()) / f"{label}.pdf"
    with temp_path.open("wb") as handle:
        writer.write(handle)
    return temp_path.read_bytes()


class TitleParserTests(unittest.TestCase):
    def test_strict_title_parser_accepts_valid_title(self) -> None:
        record = SearchDesignRecord(
            design_id="D1",
            title="완료 - 여행지 - 15 - 김민수",
            updated_at=__import__("datetime").datetime.fromisoformat("2026-03-28T09:00:00+00:00"),
        )
        parsed, issue = parse_title(record, expected_assignment_name="여행지", strict_mode=True)
        self.assertIsNone(issue)
        assert parsed is not None
        self.assertEqual(parsed.student_number, 15)
        self.assertEqual(parsed.student_name, "김민수")

    def test_strict_title_parser_accepts_hyphen_only_separator(self) -> None:
        record = SearchDesignRecord(
            design_id="D2",
            title="완료-여행지-15-김민수",
            updated_at=__import__("datetime").datetime.fromisoformat("2026-03-28T09:00:00+00:00"),
        )
        parsed, issue = parse_title(record, expected_assignment_name="여행지", strict_mode=True)
        self.assertIsNone(issue)
        assert parsed is not None
        self.assertEqual(parsed.student_number, 15)
        self.assertEqual(parsed.student_name, "김민수")


class AssignmentMergeTests(unittest.TestCase):
    def test_merge_picks_latest_duplicate_and_orders_students(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            search_results = [
                {"designId": "A1", "title": "완료 - 여행지 - 15 - 김민수", "updatedAt": "2026-03-28T09:00:00Z"},
                {"designId": "A2", "title": "완료 - 여행지 - 15 - 김민수2", "updatedAt": "2026-03-28T10:00:00Z"},
                {"designId": "B1", "title": "완료 - 여행지 - 2 - 박지은", "updatedAt": "2026-03-28T11:00:00Z"},
                {"designId": "C1", "title": "완료 - 과학 - 3 - 정우", "updatedAt": "2026-03-28T12:00:00Z"},
                {"designId": "D1", "title": "완료-여행지-20-오류", "updatedAt": "2026-03-28T13:00:00Z"},
            ]
            pdf_a2 = tmpdir_path / "a2.pdf"
            pdf_a2.write_bytes(build_pdf_bytes("A2"))
            pdf_b1 = tmpdir_path / "b1.pdf"
            pdf_b1.write_bytes(build_pdf_bytes("B1"))
            pdf_d1 = tmpdir_path / "d1.pdf"
            pdf_d1.write_bytes(build_pdf_bytes("D1"))

            client = ManifestCanvaClient(
                search_results=search_results,
                export_map={"A2": str(pdf_a2), "B1": str(pdf_b1), "D1": str(pdf_d1)},
            )
            report = run_assignment_merge(
                assignment_name="여행지",
                output_dir=tmpdir_path,
                strict_mode=True,
                client=client,
            )

            self.assertEqual(report["summary"]["totalSearchHits"], 4)
            self.assertEqual(report["summary"]["totalParsedValid"], 4)
            self.assertEqual(report["summary"]["totalExported"], 3)
            self.assertEqual(report["summary"]["duplicatesFound"], 1)
            self.assertEqual(report["finalSelectedOrder"][0]["studentNumber"], 2)
            self.assertEqual(report["finalSelectedOrder"][1]["studentNumber"], 15)
            self.assertEqual(report["finalSelectedOrder"][2]["studentNumber"], 20)
            self.assertTrue(Path(report["mergedPdfPath"]).exists())
            merged_reader = PdfReader(report["mergedPdfPath"])
            self.assertEqual(len(merged_reader.pages), 3)

    def test_non_strict_mode_allows_partial_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            search_results = [
                {"designId": "A1", "title": "완료-여행지-1-김하나", "updatedAt": "2026-03-28T09:00:00Z"},
                {"designId": "B1", "title": "완료-여행지-2-이둘", "updatedAt": "2026-03-28T10:00:00Z"},
            ]
            pdf_a1 = tmpdir_path / "a1.pdf"
            pdf_a1.write_bytes(build_pdf_bytes("A1"))
            client = ManifestCanvaClient(
                search_results=search_results,
                export_map={"A1": str(pdf_a1)},
            )

            report = run_assignment_merge(
                assignment_name="여행지",
                output_dir=tmpdir_path,
                strict_mode=False,
                client=client,
            )

            self.assertEqual(report["summary"]["totalExported"], 1)
            self.assertEqual(len(report["exportFailures"]), 1)
            self.assertTrue(Path(report["mergedPdfPath"]).exists())


if __name__ == "__main__":
    unittest.main()

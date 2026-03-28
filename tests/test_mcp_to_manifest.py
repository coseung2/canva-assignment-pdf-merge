from __future__ import annotations

import json
import unittest

from canva_assignment_merge.mcp_to_manifest import convert_mcp_search_response


class McpToManifestTests(unittest.TestCase):
    def test_happy_path_maps_realistic_search_response(self) -> None:
        raw = {
            "continuation": "token",
            "items": [
                {
                    "id": "DAGrUAXPCAI",
                    "title": "완료 - 여행지 - 15 - 김민수",
                    "updated_at": 1773724429,
                    "created_at": 1750809615,
                    "urls": {
                        "edit_url": "https://www.canva.com/d/edit",
                        "view_url": "https://www.canva.com/d/view",
                    },
                }
            ],
        }

        manifest = convert_mcp_search_response(raw)

        self.assertEqual(
            manifest,
            [
                {
                    "designId": "DAGrUAXPCAI",
                    "title": "완료 - 여행지 - 15 - 김민수",
                    "updatedAt": "2026-03-17T05:13:49Z",
                }
            ],
        )

    def test_missing_required_field_raises_value_error(self) -> None:
        raw = {"items": [{"title": "완료 - 여행지 - 15 - 김민수", "updated_at": 1773724429}]}

        with self.assertRaisesRegex(ValueError, "missing required field 'id'"):
            convert_mcp_search_response(raw)

    def test_unknown_fields_are_ignored(self) -> None:
        raw_json = json.dumps(
            {
                "items": [
                    {
                        "id": "DAHE0YwxuBA",
                        "title": "완료 - 여행지 - 2 - 박지은",
                        "updated_at": "2026-03-22T08:34:53Z",
                        "thumbnail": {"url": "https://design.canva.ai/thumb"},
                        "urls": {
                            "edit_url": "https://www.canva.com/d/edit2",
                            "view_url": "https://www.canva.com/d/view2",
                        },
                        "page_count": 2,
                        "unexpected": {"nested": True},
                    }
                ]
            },
            ensure_ascii=False,
        )

        manifest = convert_mcp_search_response(raw_json)

        self.assertEqual(
            manifest,
            [
                {
                    "designId": "DAHE0YwxuBA",
                    "title": "완료 - 여행지 - 2 - 박지은",
                    "updatedAt": "2026-03-22T08:34:53Z",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()

"""Offline checks for public updates and immutable monthly research records."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_pages
import build_research_records as records
from research_pipeline import read_json, write_json


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.item = {"arxiv_id": "2610.12345", "paper_title": "Example paper",
                     "created_at": "2026-10-31T16:00:00Z", "status": "exclude",
                     "reason": "Not enough evidence", "changes": [], "source": {"sha256": "abc"}}
        write_json(self.root / "new-papers.json", {"last_checked_at": "2026-11-01T00:00:00Z",
                                                   "papers": [{"analysis_status": "queued"}]})

    def build(self, *items):
        write_json(self.root / "research/proposals.json", {"proposals": {i["arxiv_id"]: i for i in items}})
        return records.build(self.root)

    def snapshots(self):
        return list((self.root / "research/archive").glob("*/*.json"))

    def test_only_applied_changes_are_public_with_brief_summaries(self):
        accepted = copy.deepcopy(self.item)
        accepted.update(arxiv_id="2610.54321", status="accepted", applied_at="2026-11-02T02:30:00Z")
        accepted["changes"] = [
            {"track": "en", "modality": "text", "before": None,
             "row": {"이름": "Example Bench", "평가 축": "코딩"}},
            {"track": "ko", "modality": "vision", "before": {"이름": "Other Bench", "링크": "old"},
             "row": {"이름": "Other Bench", "링크": "new"}}]
        public = self.build(self.item, accepted)
        self.assertEqual(len(public), 1)
        self.assertEqual(public[0]["applied_at"], accepted["applied_at"])
        self.assertEqual(public[0]["changes"][0]["summary"], "영어 코딩 평가 항목으로 새로 등록했습니다.")
        self.assertEqual(public[0]["changes"][1]["fields"], ["링크"])
        self.assertIn("자료 링크", public[0]["changes"][1]["summary"])
        self.assertEqual(public[0]["changes"][1]["inventory_url"], "./korean.html?modality=vision#inventory")
        data = read_json(self.root / "updates.json")
        self.assertEqual(data["last_updated_at"], accepted["applied_at"])
        self.assertNotIn(self.item["arxiv_id"], (self.root / "updates.json").read_text())
        self.assertNotIn("reason", data["updates"][0])
        self.assertEqual(len(self.snapshots()), 1)

    def test_month_is_in_korean_time_and_legacy_provenance_is_honest(self):
        self.item["validation_error"] = "Quote does not occur on cited page"
        self.build(self.item)
        path = self.snapshots()[0]
        self.assertEqual(path.parent.name, "2026-11")
        text = path.with_suffix(".md").read_text()
        self.assertIn("당시 기록에 모델명이 없음", text)
        self.assertIn("두 모델의 교차 확인 기록이 없습니다", text)
        self.assertIn(self.item["validation_error"], text)
        self.assertEqual(read_json(path)["reason"], self.item["reason"])

    def test_retries_preserve_snapshots_and_reinvestigation_appends(self):
        self.build(self.item)
        original = self.snapshots()[0]
        content = original.read_bytes()
        self.build(self.item)
        self.assertEqual(len(self.snapshots()), 1)
        self.item["reason"] = "New evidence, still insufficient"
        self.build(self.item)
        self.assertEqual(len(self.snapshots()), 2)
        self.assertEqual(original.read_bytes(), content)
        self.item.update(status="accepted", applied_at="2026-11-03T00:00:00Z")
        self.build(self.item)
        self.assertEqual(len(self.snapshots()), 2)
        self.assertEqual(original.read_bytes(), content)

    def test_no_updates_has_no_invented_date(self):
        self.build(self.item)
        data = read_json(self.root / "updates.json")
        self.assertEqual(data["updates"], [])
        self.assertIsNone(data["last_updated_at"])

    def test_votes_and_original_evidence_are_preserved(self):
        self.item.update(status="needs_evidence", extraction_model="draft-model",
                         verification={"votes": [{"model": "judge-a", "approve": True, "reason": "supported"},
                                                 {"model": "judge-b", "approve": False, "reason": "missing source"}]})
        self.build(self.item)
        path = self.snapshots()[0]
        text = path.with_suffix(".md").read_text()
        self.assertIn("judge-a: 동의", text)
        self.assertIn("judge-b: 미동의", text)
        self.assertEqual(read_json(path)["verification"], self.item["verification"])

    def test_archive_tampering_is_not_silently_overwritten(self):
        self.build(self.item)
        self.snapshots()[0].write_text('{}')
        with self.assertRaisesRegex(ValueError, "modified"):
            self.build(self.item)

    def test_public_artifact_excludes_research_queue_and_archive(self):
        self.build(self.item)
        for name in build_pages.PUBLIC:
            path = self.root / name
            if not path.exists():
                path.write_text("fixture")
        with patch.object(build_pages, "ROOT", self.root), patch.object(build_pages.subprocess, "check_output", return_value=b""):
            build_pages.main()
        site = self.root / "_site"
        self.assertTrue((site / "updates.json").exists())
        self.assertFalse((site / "new-papers.json").exists())
        self.assertFalse((site / "research").exists())


if __name__ == "__main__":
    unittest.main()

"""Exact page correction must retain evidence and require both independent votes."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import replay_citations as replay
import research_pipeline as r
import review_proposals as review
import test_research
from test_arxiv_watch import empty, paper


class CorrectionTests(unittest.TestCase):
    def draft(self, page=1, quote="Unique actual quote"):
        return {"changes": [{"track": "en", "evidence": {"언어": {"page": page, "quote": quote}}}]}

    def test_unique_quote_moves_to_actual_page(self):
        raw = self.draft()
        result, repairs = replay.correct_pages(raw, ["Unrelated page", "Unique actual quote"])
        self.assertEqual(result["changes"][0]["evidence"]["언어"]["page"], 2)
        self.assertEqual(repairs[0]["from_page"], 1)
        self.assertEqual(raw, self.draft())

    def test_ambiguous_quote_is_not_repaired(self):
        raw = self.draft()
        result, repairs = replay.correct_pages(raw, ["Unrelated", "Unique actual quote", "Unique actual quote"])
        self.assertEqual(result, raw)
        self.assertEqual(repairs, [])

    def test_absent_quote_is_not_rewritten(self):
        raw = self.draft()
        result, repairs = replay.correct_pages(raw, ["unique Actual quote"])
        self.assertEqual(result, raw)
        self.assertEqual(repairs, [])

    def test_correct_citation_unchanged_even_if_quote_repeats(self):
        raw = self.draft()
        self.assertEqual(replay.correct_pages(raw, ["Unique actual quote"] * 2), (raw, []))

    def test_invalid_page_type_remains_invalid(self):
        for value in (True, "1", None):
            raw = self.draft(page=value)
            self.assertEqual(replay.correct_pages(raw, ["Unique actual quote"]), (raw, []))

    def test_list_wrapped_citation_preserved(self):
        raw = self.draft()
        raw["changes"][0]["evidence"]["언어"] = [raw["changes"][0]["evidence"]["언어"]]
        fixed, _ = replay.correct_pages(raw, ["Unrelated", "Unique actual quote"])
        self.assertEqual(fixed["changes"][0]["evidence"]["언어"][0]["page"], 2)

    def test_model_payload_labels_every_physical_page(self):
        context = {"source": {"pages": ["first", "", "third"]}, "tables": {}}
        data = json.loads(r.evidence_payload(context))
        self.assertEqual(data["source"]["pages"], [{"page": 1, "text": "first"}, {"page": 2, "text": ""}, {"page": 3, "text": "third"}])
        self.assertEqual(context["source"]["pages"][0], "first")


class ReplayTests(unittest.TestCase):
    def setUp(self):
        # Reuse the existing inventory fixture without duplicating its schema.
        fixture = test_research.ResearchTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root = fixture.root
        self.artifact = self.root / "artifact"
        self.artifact.mkdir()
        self.key = "2610.12345"
        self.config = r.read_json(self.root / "research/config.json")
        self.config.update(enabled=True, auto_apply_agreed=True)
        r.write_json(self.root / "research/config.json", self.config)
        pages = ["Unrelated page", fixture.context["source"]["pages"][0]]
        pdf = self.artifact / f"{self.key}.pdf"
        pdf.write_bytes(b"%PDF-1.4 original fixture")
        page_file = self.artifact / f"{self.key}.pages.json"
        r.write_json(page_file, {"pages": [{"page": i + 1, "text": value} for i, value in enumerate(pages)]})
        self.old = copy.deepcopy(fixture.proposal)
        self.old.update(status="needs_evidence", changes=[], created_at="2026-10-19T00:00:00Z",
                        paper_updated=paper()["updated"], extraction_model=self.config["model"],
                        validation_error="parse: Quote does not occur on the cited PDF page")
        self.old["source"].update(sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
                                 extraction={"page_json_sha256": hashlib.sha256(page_file.read_bytes()).hexdigest()})
        self.response = self.artifact / f"{self.key}-extract.jsonl"
        self.response.write_text(json.dumps({"id": self.key, "model": self.config["model"],
            "response": json.dumps(fixture.raw), "error": self.old["validation_error"]}) + "\n")
        r.write_json(self.root / "research/proposals.json", {"proposals": {self.key: self.old}, "daily_runs": {}})
        r.save_state(self.root / "new-papers.json", {**empty(), "papers": [paper()]})

    def test_tampered_pdf_rejected(self):
        (self.artifact / f"{self.key}.pdf").write_bytes(b"different PDF")
        with self.assertRaisesRegex(ValueError, "PDF hash"):
            replay.load_evidence(self.response, self.old)

    def test_tampered_json_rejected(self):
        (self.artifact / f"{self.key}.pages.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "JSON hash"):
            replay.load_evidence(self.response, self.old)

    def test_changed_inventory_rejected(self):
        with patch.object(replay.subprocess, "check_output", return_value=b"different CSV"):
            with self.assertRaisesRegex(ValueError, "Inventory changed"):
                replay.verify_baseline(self.root, "a" * 40)

    def test_dry_run_does_not_call_models_or_write_ledger(self):
        before = (self.root / "research/proposals.json").read_bytes()
        with patch.object(replay, "verify_baseline"), patch.object(r, "provider") as provider:
            report = replay.run(self.artifact, "a" * 40, "123", self.root, dry_run=True)
        self.assertEqual(report[0]["status"], "ready")
        provider.assert_not_called()
        self.assertEqual((self.root / "research/proposals.json").read_bytes(), before)

    def verify(self, second_vote):
        models = [Mock(model=self.config["model"]), Mock(model=self.config["verifier_model"])]
        replies = [({"approve": True, "reason": "first vote"}, 0), ({"approve": second_vote, "reason": "second vote"}, 0)]
        with patch.object(replay, "verify_baseline"), patch.object(r, "provider", side_effect=models), patch.object(r, "invoke", side_effect=replies) as invoke, patch.object(r, "get_official_resource", return_value={"url": "https://example.org/data", "text": "Official evidence"}):
            replay.run(self.artifact, "a" * 40, "123", self.root)
        self.assertEqual(invoke.call_count, 2)
        calls = invoke.call_args_list
        self.assertEqual(calls[0].args[0]["messages"], calls[1].args[0]["messages"])
        self.assertNotIn("first vote", str(calls[1].args[0]))
        return r.read_json(self.root / "research/proposals.json")["proposals"][self.key]

    def test_both_votes_required_and_replay_not_repeated(self):
        result = self.verify(True)
        self.assertTrue(review.agreed(result, self.config))
        self.assertEqual(result["status"], "proposed")
        self.assertTrue(all(ev["page"] == 2 for ev in result["changes"][0]["evidence"].values()))
        with patch.object(replay, "verify_baseline"), patch.object(r, "provider") as provider:
            replay.run(self.artifact, "a" * 40, "123", self.root)
        provider.assert_not_called()

    def test_disagreement_keeps_item_out_of_inventory(self):
        result = self.verify(False)
        self.assertFalse(review.agreed(result, self.config))
        self.assertEqual(result["status"], "needs_evidence")
        self.assertEqual(result["changes"], [])


if __name__ == "__main__":
    unittest.main()

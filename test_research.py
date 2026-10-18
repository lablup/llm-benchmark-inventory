"""Offline evidence, authorization, transaction, and publication regression tests."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import arxiv_watch as watch
import research_pipeline as research
import review_proposals as review
from test_arxiv_watch import NOW, empty, paper


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        names = review.FILES + ["new-papers.json", "research/config.json", "research/proposals.json",
                 "serving_inventory.csv", "benchmark_top_models.csv", "serving_reference_values.csv"]
        for name in names:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(research.ROOT / name, target)
        tables = {track: dict(zip(("headers", "rows"), research.read_table(self.root, track))) for track in research.TABLES}
        self.context = {"tables": tables, "source": {"pages": ["Example English vision benchmark https://example.org/data"]},
                        "english_copy": (self.root / "english-copy.js").read_text()}
        row = copy.deepcopy(tables["en"]["rows"][0])
        row.update({"id": "example-bench", "이름": "Example Bench", "언어": "영어", "링크": "https://example.org/data", "예시 표기": "과제 설명", **research.UNKNOWN})
        ev = {field: {"page": 1, "quote": "Example English vision benchmark"} for field in research.CONTENT_FIELDS | {"modality"}}
        self.raw = {"decision": "propose", "reason": "새 평가 과제를 제공하는 자료입니다.", "changes": [{"track": "en", "row": row,
                   "modality": "vision", "english_copy": {k: "Example task" for k in ("axis", "definition", "task", "example")}, "evidence": ev}]}
        self.proposal = research.validate_result(copy.deepcopy(self.raw), self.context)
        self.proposal.update(arxiv_id="2610.12345", paper_title="Example Bench", status="proposed", source={"url": "https://arxiv.org/pdf/2610.12345", "sha256": "0" * 64},
                             verification={"approve": True, "reason": "Supported"}, issue_url=f"https://github.com/{watch.REPOSITORY}/issues/20")
        self.proposal["proposal_sha256"] = review.proposal_hash(self.proposal)
        self.issue = {"number": 20, "html_url": self.proposal["issue_url"], "user": {"login": "github-actions[bot]"},
                      "body": review.issue_body([self.proposal], "2026-10-18", "songys")}
        self.ledger = {"schema_version": 1, "proposals": {"2610.12345": self.proposal}, "processed_comments": []}
        self.comment = {"id": 42, "user": {"login": "songys"}, "body": "추가 2610.12345", "html_url": self.issue["html_url"] + "#issuecomment-42"}

    def test_quote_must_occur_on_exact_page(self):
        raw = copy.deepcopy(self.raw)
        raw["changes"][0]["evidence"]["언어"]["quote"] = "invented evidence"
        with self.assertRaisesRegex(ValueError, "Quote"):
            research.validate_result(raw, self.context)

    def test_language_evidence_is_required(self):
        del self.raw["changes"][0]["evidence"]["언어"]
        with self.assertRaisesRegex(ValueError, "evidence"):
            research.validate_result(self.raw, self.context)

    def test_code_license_cannot_enable_dataset_use(self):
        self.raw["changes"][0]["row"]["상업적 이용"] = "가능"
        with self.assertRaisesRegex(ValueError, "licensing"):
            research.validate_result(self.raw, self.context)

    def test_link_must_be_present_in_source(self):
        self.raw["changes"][0]["row"]["링크"] = "https://invented.example/data"
        with self.assertRaisesRegex(ValueError, "link does not occur"):
            research.validate_result(self.raw, self.context)

    def test_no_change_or_injected_columns_are_rejected(self):
        self.raw["changes"][0]["row"]["extra"] = "value"
        with self.assertRaisesRegex(ValueError, "CSV fields"):
            research.validate_result(self.raw, self.context)

    def test_no_raw_paper_notifications(self):
        github = Mock()
        github.issues.return_value = []
        result = review.sync({**empty(), "papers": [paper()]}, github, NOW, "songys", self.root)
        github.request.assert_not_called()
        self.assertEqual(result["papers"][0]["analysis_status"], "queued")
        self.assertIsNone(result["papers"][0]["review_issue_url"])

    def test_legacy_digest_does_not_generate_a_review_queue(self):
        github = Mock()
        github.issues.return_value = [{**self.issue, "body": "<!-- arxiv-review:v1:2026-10-18 -->\n- [ ] raw paper"}]
        review.sync({**empty(), "papers": [paper()]}, github, NOW, "songys", self.root)
        github.request.assert_not_called()

    def test_recover_created_issue_without_duplicate(self):
        self.proposal["issue_url"] = None
        research.write_json(self.root / "research/proposals.json", self.ledger)
        github = Mock()
        github.issues.return_value = [self.issue]
        github.request.return_value = []
        result = review.sync({**empty(), "papers": [paper()]}, github, NOW, "songys", self.root)
        self.assertEqual(result["papers"][0]["review_issue_url"], self.issue["html_url"])
        self.assertTrue(all(call.args[0].endswith("comments?per_page=100&page=1") for call in github.request.call_args_list))

    def test_exact_authorized_command_and_idempotence(self):
        apply = Mock()
        self.assertTrue(review.process_comment(self.comment, self.issue, self.ledger, "songys", self.root, apply))
        self.assertEqual(self.proposal["status"], "accepted")
        self.assertFalse(review.process_comment(self.comment, self.issue, self.ledger, "songys", self.root, apply))
        apply.assert_called_once()

    def test_other_author_and_quoted_command_have_no_effect(self):
        apply = Mock()
        for change in ({"user": {"login": "stranger"}}, {"body": "> 추가 2610.12345"}, {"body": "추가 2610.12345 해주세요"}):
            self.assertFalse(review.process_comment({**self.comment, **change}, self.issue, self.ledger, "songys", self.root, apply))
        apply.assert_not_called()

    def test_forged_issue_or_changed_proposal_has_no_effect(self):
        apply = Mock()
        forged = {**self.issue, "user": {"login": "stranger"}}
        self.assertFalse(review.process_comment(self.comment, forged, self.ledger, "songys", self.root, apply))
        self.proposal["changes"][0]["row"]["이름"] = "Changed after notification"
        self.assertFalse(review.process_comment(self.comment, self.issue, self.ledger, "songys", self.root, apply))
        apply.assert_not_called()

    def test_hold_then_accept_and_exclude_are_persisted(self):
        apply = Mock()
        held = {**self.comment, "body": "보류 2610.12345"}
        self.assertTrue(review.process_comment(held, self.issue, self.ledger, "songys", self.root, apply))
        self.assertEqual(self.proposal["status"], "held")
        self.assertTrue(review.process_comment({**self.comment, "id": 43}, self.issue, self.ledger, "songys", self.root, apply))
        apply.assert_called_once()

    def test_new_english_row_and_modality_and_copy_are_written(self):
        before = research.read_table(self.root, "en")[1]
        review.apply_proposal(self.proposal, self.root, verify=False)
        rows = research.read_table(self.root, "en")[1]
        self.assertEqual(rows[:-1], before)
        self.assertEqual(rows[-1], self.proposal["changes"][0]["row"])
        self.assertIn('"example-bench": {', (self.root / "english-copy.js").read_text())
        self.assertEqual(research.read_json(self.root / "benchmark-modalities.json")["example-bench"], "vision")

    def test_stale_row_cannot_be_overwritten(self):
        review.apply_proposal(self.proposal, self.root, verify=False)
        with self.assertRaisesRegex(ValueError, "changed after"):
            review.apply_proposal(self.proposal, self.root, verify=False)

    def test_failed_validation_rolls_back_all_writes(self):
        before = {name: (self.root / name).read_bytes() for name in review.FILES}
        with patch.object(review.subprocess, "run", side_effect=RuntimeError("validator failed")):
            with self.assertRaisesRegex(RuntimeError, "validator failed"):
                review.apply_proposal(self.proposal, self.root)
        self.assertEqual(before, {name: (self.root / name).read_bytes() for name in review.FILES})

    def test_unverified_proposal_cannot_apply(self):
        self.proposal["verification"]["approve"] = False
        with self.assertRaisesRegex(ValueError, "verification"):
            review.apply_proposal(self.proposal, self.root, verify=False)

    def test_disabled_research_never_calls_provider(self):
        with patch.object(research, "provider") as provider:
            research.run(self.root)
        provider.assert_not_called()
        self.assertEqual(watch.load_state(self.root / "new-papers.json")["research"]["status"], "not_configured")

    def test_enabled_config_needs_explicit_model_and_costs(self):
        config = research.read_json(self.root / "research/config.json")
        config["enabled"] = True
        with self.assertRaises(ValueError):
            research.check_config(config)

    def test_budget_preflight_stops_before_paid_call(self):
        with patch.object(research, "estimate_cost", return_value=2), patch.object(research, "run_batch") as batch:
            with self.assertRaisesRegex(ValueError, "budget"):
                research.invoke({}, Mock(), self.root / "out.jsonl", json.loads, 1)
        batch.assert_not_called()

    def test_complete_apply_regenerates_and_validates_public_data(self):
        import validate_inventory
        for name in validate_inventory.REQUIRED_PAGES + ["arxiv_watch.py", "research_pipeline.py", "review_proposals.py", "build_site_data.py", "build_benchmark_inventory.py", "validate_inventory.py", "vendor/llm_batch.py"]:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(research.ROOT / name, target)
        review.apply_proposal(self.proposal, self.root)
        self.assertIn("Example Bench", (self.root / "README.md").read_text())
        self.assertIn('"입력 유형":"vision"', (self.root / "inventory-data.js").read_text())
        self.assertIn('"english_count":32', (self.root / "site-meta.js").read_text())
        self.assertIn('"english_vision_count":5', (self.root / "site-meta.js").read_text())

    def test_two_model_passes_use_shared_runner_and_day_limit(self):
        config = {"enabled": True, "provider": "openrouter", "model": "fixture", "price_in_per_million": 1,
                  "price_out_per_million": 1, "cost_cap_usd": 1, "daily_papers": 1}
        research.write_json(self.root / "research/config.json", config)
        watch.save_state(self.root / "new-papers.json", {**empty(), "papers": [paper()]})
        transport = Mock(side_effect=[{"text": json.dumps(self.raw), "usage": {}, "cost": .001},
                                     {"text": '{"approve":true,"reason":"Supported"}', "usage": {}, "cost": .001}])
        provider = research.Provider(name="fixture", model="fixture", transport=transport, max_tokens=6000,
                                     price_in=.000001, price_out=.000001)
        source = {**self.context["source"], "url": "https://arxiv.org/pdf/2610.12345", "sha256": "0" * 64}
        with patch.object(research, "provider", return_value=provider), patch.object(research, "get_pdf", return_value=source), patch.object(research, "get_official_resource", return_value={"url": "https://example.org/data", "text": "Official card"}), patch.object(research.time, "sleep"):
            research.run(self.root)
            research.run(self.root)
        self.assertEqual(transport.call_count, 2)
        ledger = research.read_json(self.root / "research/proposals.json")
        self.assertEqual(ledger["proposals"]["2610.12345"]["status"], "proposed")
        self.assertEqual(next(iter(ledger["daily_runs"].values()))["spent_usd"], .002)

    def test_official_source_adapter_rejects_arbitrary_hosts_without_request(self):
        with patch.object(research, "build_opener") as opener:
            for url in ["https://localhost/data", "http://github.com/a/b", "https://github.com@localhost/a/b", "https://github.com:444/a/b"]:
                with self.assertRaises(ValueError):
                    research.get_official_resource(url)
        opener.assert_not_called()

    def test_notification_contains_actual_diff_and_no_checkbox(self):
        body = self.issue["body"]
        self.assertIn("| 항목 | 현재 | 변경 후 |", body)
        self.assertIn("추가 2610.12345", body)
        self.assertNotIn("- [ ]", body)
        self.assertEqual(body.count("Example English vision benchmark"), 1)


if __name__ == "__main__":
    unittest.main()

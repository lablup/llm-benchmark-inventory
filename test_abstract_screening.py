"""Abstract-only gating, resumability and language/modality publication checks."""
import copy
import json
import unittest
from unittest.mock import Mock, patch
from datetime import timedelta

import arxiv_watch as watch
import build_research_records as records
import research_pipeline as research
import review_proposals as review
import test_research as fixtures
from test_arxiv_watch import empty, paper


class ScreeningTests(unittest.TestCase):
    setUp = fixtures.ResearchTests.setUp

    def prepare(self, count=1, daily_papers=100):
        self.config = research.read_json(self.root / "research/config.json")
        self.config.update(enabled=True, auto_apply_agreed=True, daily_papers=daily_papers,
                           daily_abstracts=1000, abstract_batch_size=20, run_minutes=90)
        research.write_json(self.root / "research/config.json", self.config)
        self.papers = []
        for i in range(count):
            p = paper()
            p.update(arxiv_id=f"2610.{12345+i:05d}", url=f"https://arxiv.org/abs/2610.{12345+i:05d}")
            self.papers.append(p)
        watch.save_state(self.root / "new-papers.json", {**empty(), "papers": self.papers})
        self.primary = research.Provider(name="fixture", model=self.config["model"], price_in=0, price_out=0)
        self.secondary = research.Provider(name="fixture", model=self.config["verifier_model"], price_in=0, price_out=0)

    def votes(self, decision):
        return {p["arxiv_id"]: {"decision": decision, "reason": decision} for p in self.papers}

    def run_replies(self, replies, pdf_error=None):
        primary = self.primary
        def model(config, name=None):
            return self.secondary if name else primary
        with patch.object(research, "provider", side_effect=model), patch.object(research, "invoke", side_effect=replies) as invoke, patch.object(research, "get_pdf", side_effect=pdf_error) as pdf, patch.object(research.time, "sleep"):
            research.run(self.root)
        return invoke, pdf

    def test_both_models_exclude_without_pdf_or_inventory_payload(self):
        self.prepare(2)
        invoke, pdf = self.run_replies([(self.votes("irrelevant"), 0), (self.votes("irrelevant"), 0)])
        pdf.assert_not_called()
        self.assertEqual(invoke.call_count, 2)
        first, second = invoke.call_args_list
        self.assertEqual(first.args[0]["messages"], second.args[0]["messages"])
        payload = first.args[0]["messages"][1]["content"]
        for paper in self.papers:
            self.assertIn(f"Paper ID: {paper['arxiv_id']}", payload)
            self.assertIn(paper["summary"], payload)
        self.assertNotIn("tables", payload)
        self.assertNotIn("pdf_url", payload)
        self.assertEqual(first.args[1].max_tokens, 3000)
        schema = first.args[1].response_format["json_schema"]["schema"]
        rows = schema["properties"]["papers"]
        self.assertEqual(rows["minItems"], 2)
        self.assertEqual(set(rows["items"]["properties"]["arxiv_id"]["enum"]),
                         {p["arxiv_id"] for p in self.papers})
        ledger = research.read_json(self.root / "research/proposals.json")
        self.assertEqual(len(ledger["screenings"]), 2)
        self.assertEqual(ledger["proposals"], {})
        records.build(self.root)
        archived = list((self.root / "research/archive").glob("*/*abstract*.md"))
        self.assertEqual(len(archived), 2)
        self.assertIn("PDF 본문은 읽지 않음", archived[0].read_text())
        self.assertEqual(research.read_json(self.root / "updates.json")["updates"], [])

    def test_next_day_reuses_completed_screening_without_model_or_pdf_calls(self):
        self.prepare()
        self.run_replies([(self.votes("irrelevant"), 0), (self.votes("irrelevant"), 0)])
        tomorrow = research.datetime.now(research.timezone.utc) + timedelta(days=1)
        with patch.object(research, "datetime") as clock:
            clock.now.return_value = tomorrow
            invoke, pdf = self.run_replies([])
        invoke.assert_not_called()
        pdf.assert_not_called()

    def test_next_day_never_reinvestigates_completed_full_text(self):
        self.prepare()
        item = copy.deepcopy(self.proposal)
        item["status"] = "accepted"
        research.write_json(self.root / "research/proposals.json", {"proposals": {item["arxiv_id"]: item}})
        tomorrow = research.datetime.now(research.timezone.utc) + timedelta(days=1)
        with patch.object(research, "datetime") as clock:
            clock.now.return_value = tomorrow
            invoke, pdf = self.run_replies([])
        invoke.assert_not_called()
        pdf.assert_not_called()

    def test_rss_oai_date_enrichment_reuses_legacy_abstract_decision(self):
        self.prepare()
        paper = self.papers[0]
        legacy = research.digest({"paper": research.abstract_input(paper),
            "prompt": research.SCREEN_PROMPT, "version": research.SCREEN_VERSION,
            "models": [self.config["model"], self.config["verifier_model"]]})
        record = {"input_sha256": legacy, "paper_title": paper["title"],
                  "abstract": paper["summary"], "paper_updated": paper["updated"]}
        enriched = {**paper, "updated": None, "announced_at": "2026-10-17T04:00:00Z"}
        self.assertTrue(research.screening_matches(record, enriched, self.config))
        self.assertFalse(research.screening_matches(record, {**enriched, "summary": "Changed"}, self.config))
        self.assertEqual(research.screening_hash(paper, self.config), research.screening_hash(enriched, self.config))

    def test_disagreement_or_uncertainty_goes_to_full_text(self):
        for decision in ("relevant", "uncertain"):
            with self.subTest(decision=decision):
                self.prepare()
                research.write_json(self.root / "research/proposals.json", {"proposals": {}, "daily_runs": {}})
                _, pdf = self.run_replies([(self.votes("irrelevant"), 0), (self.votes(decision), 0)], pdf_error=ValueError("unavailable"))
                pdf.assert_called_once()
                ledger = research.read_json(self.root / "research/proposals.json")
                self.assertEqual(ledger["screenings"][self.papers[0]["arxiv_id"]]["status"], "passed")
                self.assertFalse(next(iter(ledger["daily_runs"].values())).get("blocked"))

    def test_malformed_screening_never_excludes(self):
        self.prepare()
        _, pdf = self.run_replies([research.EvidenceRejected("bad schema", 0), (self.votes("irrelevant"), 0)], pdf_error=ValueError("unavailable"))
        pdf.assert_called_once()

    def test_same_day_resume_does_not_repeat_model_calls(self):
        self.prepare()
        self.run_replies([(self.votes("irrelevant"), 0), (self.votes("irrelevant"), 0)])
        invoke, pdf = self.run_replies([])
        invoke.assert_not_called()
        pdf.assert_not_called()

    def test_more_than_five_papers_can_reach_full_text(self):
        self.prepare(8)
        _, pdf = self.run_replies([(self.votes("relevant"), 0), (self.votes("uncertain"), 0)], pdf_error=ValueError("fixture PDF failure"))
        self.assertEqual(pdf.call_count, 8)
        ledger = research.read_json(self.root / "research/proposals.json")
        day = next(iter(ledger["daily_runs"].values()))
        self.assertEqual(len(day["abstract_attempted"]), 8)
        self.assertEqual(len(day["attempted"]), 8)

    def test_separate_abstract_and_body_limits(self):
        self.prepare(3, daily_papers=1)
        _, pdf = self.run_replies([(self.votes("relevant"), 0), (self.votes("relevant"), 0)], pdf_error=ValueError("fixture PDF failure"))
        self.assertEqual(pdf.call_count, 1)
        ledger = research.read_json(self.root / "research/proposals.json")
        self.assertEqual(len(ledger["screenings"]), 3)
        self.assertEqual(len(next(iter(ledger["daily_runs"].values()))["attempted"]), 1)

    def test_strict_ids_and_duplicate_detection(self):
        valid = {"arxiv_id": "2610.12345", "decision": "relevant", "reason": "Useful benchmark"}
        self.assertEqual(research.parse_screening(json.dumps({"papers": [valid]}), [valid["arxiv_id"]])[valid["arxiv_id"]]["decision"], "relevant")
        for rows in ([], [valid, valid], [{**valid, "arxiv_id": "2610.99999"}], [{**valid, "decision": "approve"}]):
            with self.assertRaises(ValueError):
                research.parse_screening(json.dumps({"papers": rows}), [valid["arxiv_id"]])

    def test_time_budget_stops_without_marking_unstarted_work_complete(self):
        self.prepare()
        state = watch.load_state(self.root / "new-papers.json")
        ledger = {"proposals": {}, "daily_runs": {"2026-10-19": {"spent_usd": 0, "attempted": []}}}
        with patch.object(research, "invoke") as invoke:
            research.screen_candidates(state, ledger, self.config, self.primary, self.secondary,
                                       self.root, "2026-10-19", deadline=-1)
        invoke.assert_not_called()
        self.assertEqual(ledger["screenings"], {})
        self.assertEqual(ledger["daily_runs"]["2026-10-19"]["abstract_attempted"], [])

    def test_transport_failure_retains_stop_checkpoint(self):
        self.prepare()
        with self.assertRaises(RuntimeError):
            self.run_replies([RuntimeError("network error")])
        ledger = research.read_json(self.root / "research/proposals.json")
        self.assertTrue(next(iter(ledger["daily_runs"].values()))["blocked"])
        self.assertEqual(ledger["screenings"], {})

    def test_changed_abstract_invalidates_prior_screening(self):
        self.prepare()
        changed = {**self.papers[0], "summary": "New abstract"}
        self.assertNotEqual(research.screening_hash(changed, self.config), research.screening_hash(self.papers[0], self.config))

    def test_shared_runner_performs_abstract_passes_then_full_text(self):
        self.prepare()
        text = json.dumps({"papers": [{"arxiv_id": self.papers[0]["arxiv_id"], "decision": "uncertain", "reason": "Need full text"}]})
        transport = Mock(return_value={"text": text, "usage": {}, "cost": 0})
        self.primary.transport = transport
        self.secondary.transport = transport
        with patch.object(research, "provider", side_effect=[self.primary, self.secondary]), patch.object(research, "get_pdf", side_effect=ValueError("fixture")) as pdf, patch.object(research.time, "sleep"):
            research.run(self.root)
        self.assertEqual(transport.call_count, 2)
        pdf.assert_called_once()

    def test_full_text_requires_independent_agreement_after_abstract_pass(self):
        self.prepare()
        source = {**self.context["source"], "url": "https://arxiv.org/pdf/2610.12345", "sha256": "0" * 64}
        proposal = copy.deepcopy(self.proposal)
        proposal.pop("verification")
        replies = [(self.votes("relevant"), 0), (self.votes("relevant"), 0),
                   (proposal, 0), ({"approve": True, "reason": "supported"}, 0),
                   ({"approve": False, "reason": "wrong language evidence"}, 0)]
        with patch.object(research, "provider", side_effect=[self.primary, self.secondary]), patch.object(research, "invoke", side_effect=replies), patch.object(research, "get_pdf", return_value=source), patch.object(research, "get_official_resource", return_value={"text": "Official card"}), patch.object(research.time, "sleep"):
            research.run(self.root)
        item = research.read_json(self.root / "research/proposals.json")["proposals"]["2610.12345"]
        self.assertEqual(item["status"], "needs_evidence")
        self.assertEqual(item["changes"], [])
        self.assertFalse(review.agreed(item, self.config))

    def test_screening_smoke_limits_to_ten_and_never_downloads_pdf(self):
        self.prepare(14)
        replies = [(self.votes("relevant"), 0), (self.votes("relevant"), 0)]
        with patch.object(research, "provider", side_effect=[self.primary, self.secondary]), patch.object(research, "invoke", side_effect=replies) as invoke, patch.object(research, "get_pdf") as pdf:
            research.run(self.root, screening_smoke=True)
        pdf.assert_not_called()
        payload = invoke.call_args_list[0].args[0]["messages"][1]["content"]
        self.assertEqual(payload.count("Paper ID: "), 10)
        ledger = research.read_json(self.root / "research/proposals.json")
        self.assertEqual(len(ledger["screenings"]), 10)
        self.assertEqual(next(iter(ledger["daily_runs"].values()))["attempted"], [])

    def test_all_language_and_modality_routes_rebuild_correct_public_rows(self):
        import shutil
        import validate_inventory
        for name in validate_inventory.REQUIRED_PAGES + ["arxiv_watch.py", "research_pipeline.py", "pdf_evidence.py", "review_proposals.py", "build_site_data.py", "build_benchmark_inventory.py", "validate_inventory.py", "serving_watch.py", "serving-watch-sources.json", "vendor/llm_batch.py"]:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(research.ROOT / name, target)
        ledger = {"proposals": {}}
        for i, (track, modality) in enumerate((("ko", "text"), ("en", "text"), ("ko", "vision"), ("en", "vision"))):
            with self.subTest(track=track, modality=modality):
                context = copy.deepcopy(self.context)
                context["source"]["pages"] = ["Example Korean English text vision benchmark https://example.org/data"]
                raw = copy.deepcopy(self.raw)
                change = raw["changes"][0]
                change.update(track=track, modality=modality)
                change["row"] = copy.deepcopy(context["tables"][track]["rows"][0])
                key = f"fixture-{track}-{modality}"
                change["row"].update({"id": key, "이름": key, "언어": track,
                                      "링크": "https://example.org/data", "예시 표기": "과제 설명",
                                      "이용 시 유의사항": "이용 조건과 평가 도구 지원은 미확인", **research.UNKNOWN})
                for ev in change["evidence"].values():
                    ev["quote"] = "Example Korean English text vision benchmark"
                item = research.validate_result(raw, context)
                item.update(arxiv_id=f"2610.{20000+i}", paper_title=key, source={"url": "https://arxiv.org/pdf/2610.20000", "sha256": "0"*64},
                            status="accepted", applied_at="2026-10-19T02:30:00Z", verification={"approve": True})
                item["proposal_sha256"] = review.proposal_hash(item)
                review.apply_proposal(item, self.root)
                data = json.loads((self.root / "inventory-data.js").read_text().split(" = ", 1)[1].rstrip(";\n"))
                row = next(r for r in data if r["id"] == key)
                self.assertEqual((row["트랙"], row["입력 유형"]), (track, modality))
                other = "en" if track == "ko" else "ko"
                self.assertFalse(any(r["id"] == key for r in research.read_table(self.root, other)[1]))
                ledger["proposals"][item["arxiv_id"]] = item
        research.write_json(self.root / "research/proposals.json", ledger)
        updates = records.build(self.root)
        destinations = {u["changes"][0]["inventory_url"] for u in updates}
        self.assertEqual(destinations, {"./korean.html#inventory", "./english.html#inventory",
                                       "./korean.html?modality=vision#inventory", "./english.html?modality=vision#inventory"})


if __name__ == "__main__":
    unittest.main()

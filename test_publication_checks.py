"""Regression tests for complete publication evidence and atomic model scores."""
import copy
import unittest
from unittest.mock import patch

import claude_approval as claude
import publication_checks as p
import research_pipeline as r
import review_proposals as review
import test_research
from test_arxiv_watch import empty, paper


class PublicationTests(unittest.TestCase):
    def setUp(self):
        fixture = test_research.ResearchTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root, self.context, self.raw = fixture.root, fixture.context, copy.deepcopy(fixture.raw)
        self.context["source"].update(url="https://arxiv.org/pdf/2610.12345", sha256="0" * 64)
        text = "Dataset license permits these uses. Harness explicitly supported. Model A 90. Model B 80. Public weights for Model B."
        self.context["source"]["pages"].append(text)
        change = self.raw["changes"][0]
        change["row"].update({"라이선스": "Documented dataset license", "상업적 이용": "가능",
                              "수정·파생": "가능", "재배포": "가능", "lm-eval 지원": "지원",
                              "이용 시 유의사항": "문서에 명시된 이용 조건 준수"})
        change["rights_evidence"] = {k: {"page": 2, "quote": "Dataset license permits these uses."}
                                    for k in r.UNKNOWN}
        change["rights_evidence"]["lm-eval 지원"]["quote"] = "Harness explicitly supported."
        change["recommendations"] = {
            "metric": "accuracy (%)", "setting": "Paper table 1, test split, zero-shot", "higher_is_better": True,
            "results": [
                {"model": "Model B", "score": "80", "open_weight": True,
                 "evidence": {"page": 2, "quote": "Model B 80."},
                 "open_weight_evidence": {"page": 2, "quote": "Public weights for Model B."}},
                {"model": "Model A", "score": "90", "open_weight": None,
                 "evidence": {"page": 2, "quote": "Model A 90."}}]}
        self.config = r.read_json(r.ROOT / "research/config.json")
        r.write_json(self.root / "research/config.json", self.config)

    def validated(self):
        return p.validate(copy.deepcopy(self.raw), self.context, self.root)

    def item(self):
        proposal = self.validated()
        proposal.update(arxiv_id="2610.12345", paper_title="Fixture paper", paper_updated="2026-10-20",
                        source={k: v for k, v in self.context["source"].items() if k != "pages"}, status="proposed")
        proposal["proposal_sha256"] = review.proposal_hash(proposal)
        proposal["verification"] = {"policy": "claude_only", "publication_policy": p.POLICY, "approve": True,
                                    "reviewed_sha256": proposal["proposal_sha256"],
                                    "votes": [{"model": claude.MODEL, "approve": True, "auth_method": "oauth_token"}]}
        return proposal

    def test_unknown_and_synonyms_block_publication_even_after_approval(self):
        for unknown in ("확인 불가", "미확인", "unknown"):
            with self.subTest(unknown=unknown):
                item = self.item()
                item["changes"][0]["row"]["라이선스"] = unknown
                item["proposal_sha256"] = review.proposal_hash(item)
                item["verification"]["reviewed_sha256"] = item["proposal_sha256"]
                self.assertFalse(review.agreed(item, self.config))
                with self.assertRaisesRegex(ValueError, "Unconfirmed"):
                    review.apply_proposal(item, self.root, verify=False)

    def test_old_claude_approval_does_not_meet_new_policy(self):
        item = self.item()
        del item["verification"]["publication_policy"]
        self.assertFalse(review.agreed(item, self.config))

    def test_missing_scores_and_missing_rights_cannot_pass(self):
        for field in ("recommendations", "rights_evidence"):
            raw = copy.deepcopy(self.raw)
            del raw["changes"][0][field]
            with self.assertRaises(ValueError):
                p.validate(raw, self.context, self.root)

    def test_unfetched_official_card_cannot_support_rights(self):
        self.raw["changes"][0]["rights_evidence"]["라이선스"] = {
            "source_url": "https://invented.example/license", "quote": "MIT"}
        with self.assertRaisesRegex(ValueError, "not fetched"):
            self.validated()

    def test_wrong_page_or_score_cannot_pass(self):
        result = self.raw["changes"][0]["recommendations"]["results"][0]
        result["score"] = "8"
        with self.assertRaisesRegex(ValueError, "exact model and numeric"):
            self.validated()
        result["score"] = "80"
        result["evidence"]["page"] = 1
        with self.assertRaisesRegex(ValueError, "absent"):
            self.validated()

    def test_unsupported_weight_classification_cannot_pass(self):
        del self.raw["changes"][0]["recommendations"]["results"][0]["open_weight_evidence"]
        with self.assertRaisesRegex(ValueError, "weight claims"):
            self.validated()

    def test_atomic_application_includes_sorted_scores_and_keeps_other_benchmarks(self):
        item = self.item()
        before = p.read_rankings(self.root)
        self.assertTrue(review.agreed(item, self.config))
        review.apply_proposal(item, self.root, verify=False)
        rows = p.read_rankings(self.root)
        self.assertEqual([x for x in rows if x["benchmark_id"] != "example-bench"], before)
        new = [x for x in rows if x["benchmark_id"] == "example-bench"]
        self.assertEqual([(x["scope"], x["model"], x["score"]) for x in new],
                         [("all", "Model A", "90"), ("all", "Model B", "80"), ("open_weight", "Model B", "80")])
        import build_site_data
        with patch.object(build_site_data, "ROOT", self.root):
            record = {"id": "example-bench"}
            build_site_data.attach_recommended([record])
        self.assertEqual(record["추천 모델"]["all"][0]["score"], 90.0)
        self.assertEqual(record["추천 모델"]["metric"], "accuracy (%)")

    def test_lower_is_better_ranking(self):
        self.raw["changes"][0]["recommendations"]["higher_is_better"] = False
        review.apply_proposal(self.item(), self.root, verify=False)
        first = next(x for x in p.read_rankings(self.root) if x["benchmark_id"] == "example-bench")
        self.assertEqual(first["model"], "Model B")

    def test_stale_scores_roll_back_inventory_and_copy(self):
        item = self.item()
        item["changes"][0]["recommendations_before_sha256"] = "changed"
        item["proposal_sha256"] = review.proposal_hash(item)
        item["verification"]["reviewed_sha256"] = item["proposal_sha256"]
        before = {name: (self.root / name).read_bytes() for name in review.FILES}
        with self.assertRaisesRegex(ValueError, "scores changed"):
            review.apply_proposal(item, self.root, verify=False)
        self.assertEqual(before, {name: (self.root / name).read_bytes() for name in review.FILES})

    def test_validation_failure_rolls_back_scores_too(self):
        before = {name: (self.root / name).read_bytes() for name in review.FILES}
        with patch.object(review.subprocess, "run", side_effect=RuntimeError("validation failed")):
            with self.assertRaises(RuntimeError):
                review.apply_proposal(self.item(), self.root)
        self.assertEqual(before, {name: (self.root / name).read_bytes() for name in review.FILES})

    def test_incomplete_enrichment_is_held_without_requesting_approval(self):
        ledger, state = {"proposals": {}, "screenings": {}}, {**empty(), "papers": [paper()]}
        draft = copy.deepcopy(self.raw)
        for change in draft["changes"]:
            change.pop("recommendations")
            change.pop("rights_evidence")
            change["row"].update(r.UNKNOWN)
        with patch.object(claude, "call", return_value={"decision": "needs_evidence", "reason": "License not documented", "changes": []}) as call:
            item = claude.audit_and_save(self.root, ledger, state, state["papers"][0],
                                         draft, self.context, self.config, claude.MODEL)
        call.assert_called_once()
        self.assertEqual(item["status"], "needs_evidence")
        self.assertNotIn("verification", item)

    def test_complete_proposal_is_bound_to_new_claude_approval(self):
        ledger, state = {"proposals": {}, "screenings": {}}, {**empty(), "papers": [paper()]}
        vote = {"model": claude.MODEL, "approve": True, "reason": "Supported", "auth_method": "oauth_token"}
        with patch.object(claude, "call", return_value=vote):
            item = claude.audit_and_save(self.root, ledger, state, state["papers"][0],
                                         self.validated(), self.context, self.config, claude.MODEL)
        self.assertTrue(review.agreed(item, self.config))
        item["changes"][0]["recommendations"]["results"][0]["score"] = "99"
        self.assertFalse(review.agreed(item, self.config))

    def test_scheduled_pipeline_completes_then_audits_and_applies_scores(self):
        state = {**empty(), "papers": [paper()]}
        candidate = state["papers"][0]
        ledger = {"proposals": {}, "screenings": {candidate["arxiv_id"]: {
            "status": "passed", "paper_title": candidate["title"], "abstract": candidate["summary"]}}}
        r.write_json(self.root / "research/proposals.json", ledger)
        r.save_state(self.root / "new-papers.json", state)
        draft = copy.deepcopy(self.raw)
        for change in draft["changes"]:
            change["row"].update(r.UNKNOWN)
            change.pop("rights_evidence")
            change.pop("recommendations")
        vote = {"model": claude.MODEL, "approve": True, "reason": "Supported", "auth_method": "oauth_token"}
        with patch.object(claude, "call", side_effect=[draft, self.validated(), vote]) as call, \
                patch.object(r, "get_pdf", return_value=self.context["source"]), \
                patch.object(r, "get_official_resource", return_value={"url": "https://example.org/data", "text": "Official card"}):
            r.run(self.root)
        self.assertEqual(call.call_count, 3)
        self.assertIn("Model A", call.call_args_list[2].args[0])
        item = r.read_json(self.root / "research/proposals.json")["proposals"][candidate["arxiv_id"]]
        self.assertTrue(review.agreed(item, self.config))
        review.apply_proposal(item, self.root, verify=False)
        self.assertEqual(sum(row["benchmark_id"] == "example-bench" for row in p.read_rankings(self.root)), 3)


if __name__ == "__main__":
    unittest.main()

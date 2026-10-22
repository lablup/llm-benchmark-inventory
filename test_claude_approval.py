"""Production approval policy, interruption recovery and subscription isolation."""
import copy
import json
import time
import unittest
from unittest.mock import Mock, patch

import claude_approval as c
import research_pipeline as r
import review_proposals as review
from test_arxiv_watch import empty, paper
import test_research


class ClaudeApprovalTests(unittest.TestCase):
    def setUp(self):
        fixture = test_research.ResearchTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root, self.raw, self.context = fixture.root, fixture.raw, fixture.context
        self.config = r.read_json(r.ROOT / "research/config.json")
        self.config.pop("publication_policy", None)
        self.config.update(enabled=True, daily_papers=1)
        r.write_json(self.root / "research/config.json", self.config)
        self.context["source"].update(url="https://arxiv.org/pdf/2610.12345", sha256="0" * 64)
        self.state = {**empty(), "papers": [paper()]}
        self.proposal = r.validate_result(copy.deepcopy(self.raw), self.context)
        self.ledger = {"proposals": {}, "daily_runs": {}, "screenings": {}}
        self.vote = {"model": c.MODEL, "approve": True, "reason": "근거 확인", "auth_method": "oauth_token"}

    def audit(self):
        return c.audit_and_save(self.root, self.ledger, self.state, self.state["papers"][0],
                                self.proposal, self.context, self.config, c.MODEL)

    def test_claude_alone_authorizes_exact_proposal(self):
        with patch.object(c, "call", return_value=self.vote):
            item = self.audit()
        self.assertTrue(review.agreed(item, self.config))
        item["changes"][0]["row"]["정의"] += "unsupported change"
        self.assertFalse(review.agreed(item, self.config))

    def test_legacy_votes_and_wrong_auth_cannot_authorize(self):
        with patch.object(c, "call", return_value=self.vote):
            item = self.audit()
        item["verification"]["votes"][0]["auth_method"] = "api_key"
        self.assertFalse(review.agreed(item, self.config))
        item["verification"].update(policy="dual_model", votes=[
            {"model": test_research.LEGACY_CONFIG[k], "approve": True} for k in ("model", "verifier_model")])
        self.assertFalse(review.agreed(item, self.config))

    def test_rejection_is_held_and_not_applied(self):
        with patch.object(c, "call", return_value={**self.vote, "approve": False}):
            item = self.audit()
        self.assertEqual(item["status"], "needs_evidence")
        self.assertFalse(review.agreed(item, self.config))

    def test_interrupted_audit_resumes_without_draft_call(self):
        with patch.object(c, "call", side_effect=RuntimeError("quota")):
            with self.assertRaisesRegex(RuntimeError, "quota"):
                self.audit()
        ledger = r.read_json(self.root / "research/proposals.json")
        self.assertEqual(ledger["proposals"]["2610.12345"]["status"], "awaiting_claude")
        with patch.object(c, "call", return_value=self.vote) as call:
            c.resume_pending(self.root, ledger, self.state, self.config, time.monotonic() + 20)
        call.assert_called_once()
        self.assertTrue(review.agreed(ledger["proposals"]["2610.12345"], self.config))

    def test_changed_pending_context_is_rejected(self):
        with patch.object(c, "call", side_effect=RuntimeError("quota")):
            with self.assertRaises(RuntimeError):
                self.audit()
        path = self.root / ".research-cache/claude/2610.12345/context.json"
        context = r.read_json(path)
        context["source"]["pages"][0] += "forged"
        r.write_json(path, context)
        with patch.object(c, "call") as call:
            c.resume_pending(self.root, self.ledger, self.state, self.config, time.monotonic() + 20)
        call.assert_not_called()
        item = r.read_json(self.root / "research/proposals.json")["proposals"]["2610.12345"]
        self.assertEqual(item["status"], "needs_evidence")
        self.assertNotIn("claude_pending", item)
        self.assertIn("context hash", item["resume_error"])
        self.assertEqual(r.load_state(self.root / "new-papers.json")["papers"][0]["analysis_status"], "needs_evidence")

    def test_one_stale_draft_holds_only_itself_and_later_candidates_still_resume(self):
        pending = {**self.proposal, "arxiv_id": "2610.00001", "status": "awaiting_claude",
                   "claude_pending": {"source_run": "1", "context_sha256": "x"}}
        self.ledger["proposals"]["2610.00001"] = pending
        self.ledger["proposals"]["2610.00002"] = {**copy.deepcopy(pending), "arxiv_id": "2610.00002"}
        self.state["papers"] += [paper("2610.00001"), paper("2610.00002")]
        with patch.object(c, "resume_one", side_effect=[ValueError("Automatic proposals cannot assert new licensing"), None]) as resume:
            c.resume_pending(self.root, self.ledger, self.state, self.config, time.monotonic() + 20)
        self.assertEqual([call.args[4] for call in resume.call_args_list], ["2610.00001", "2610.00002"])
        held = self.ledger["proposals"]["2610.00001"]
        self.assertEqual(held["status"], "needs_evidence")
        self.assertIn("재감사", held["reason"])
        self.assertEqual(self.ledger["proposals"]["2610.00002"]["status"], "awaiting_claude")
        # A quota or token failure still stops the run so the budget checkpoint is kept.
        with patch.object(c, "resume_one", side_effect=RuntimeError("quota")), self.assertRaisesRegex(RuntimeError, "quota"):
            c.resume_pending(self.root, self.ledger, self.state, self.config, time.monotonic() + 20)

    def test_no_oauth_token_means_no_subprocess_or_api(self):
        with patch.dict(c.os.environ, {"ANTHROPIC_API_KEY": "not-allowed"}, clear=True), patch.object(c.subprocess, "run") as process:
            with self.assertRaisesRegex(RuntimeError, "token is missing"):
                c.call("test", self.root / "cache")
        process.assert_not_called()

    def test_cli_uses_only_oauth_and_reuses_complete_answer(self):
        messages = [{"type": "system", "subtype": "init", "model": c.MODEL},
                    {"type": "result", "subtype": "success", "is_error": False,
                     "num_turns": 1, "result": '{"approve":true,"reason":"Supported"}'}]
        calls = [Mock(returncode=0, stdout='{"authMethod":"oauth_token"}'),
                 Mock(returncode=0, stdout="\n".join(json.dumps(m) for m in messages))]
        with patch.dict(c.os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "test-token", "ANTHROPIC_API_KEY": "forbidden",
                                     "ANTHROPIC_BASE_URL": "https://invalid", "CLAUDE_CODE_USE_BEDROCK": "1"}), \
                patch.object(c.subprocess, "run", side_effect=calls) as process:
            first = c.call("test prompt", self.root / "cache")
            second = c.call("test prompt", self.root / "cache")
        self.assertEqual(first, second)
        self.assertEqual(process.call_count, 2)
        env = process.call_args.kwargs["env"]
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("CLAUDE_CODE_USE_BEDROCK", env)
        self.assertNotIn("ANTHROPIC_BASE_URL", env)
        self.assertEqual(env["CLAUDE_CODE_OAUTH_TOKEN"], "test-token")

    def test_production_uses_no_token_factory_calls(self):
        p = self.state["papers"][0]
        self.ledger["screenings"][p["arxiv_id"]] = {
            "status": "passed", "paper_title": p["title"], "abstract": p["summary"]}
        r.write_json(self.root / "research/proposals.json", self.ledger)
        r.save_state(self.root / "new-papers.json", self.state)
        with patch.object(r, "provider") as provider, patch.object(r, "get_pdf", return_value=self.context["source"]), \
                patch.object(r, "get_official_resource", return_value={"url": "https://example.org/data", "text": "Official"}), \
                patch.object(c, "call", side_effect=[self.proposal, self.vote]) as call:
            r.run(self.root)
            r.run(self.root)
        provider.assert_not_called()
        self.assertEqual(call.call_count, 2)
        item = r.read_json(self.root / "research/proposals.json")["proposals"][p["arxiv_id"]]
        self.assertTrue(review.agreed(item, self.config))

    def test_reaudit_reprocesses_a_held_candidate_under_the_current_policy(self):
        p = self.state["papers"][0]
        self.ledger["screenings"][p["arxiv_id"]] = {"status": "passed", "paper_title": p["title"], "abstract": p["summary"]}
        held = {**self.proposal, "arxiv_id": p["arxiv_id"], "status": "held", "reason": "사용자 보류"}
        self.ledger["proposals"][p["arxiv_id"]] = held
        self.ledger["claude_daily_runs"] = {time.strftime("%Y-%m-%d"): {"attempted": [p["arxiv_id"]], "abstract_attempted": []}}
        p.update(analysis_status="held")
        r.write_json(self.root / "research/proposals.json", self.ledger)
        r.save_state(self.root / "new-papers.json", self.state)
        with patch.object(r, "get_pdf", return_value=self.context["source"]), \
                patch.object(r, "get_official_resource", return_value={"url": "https://example.org/data", "license_file": None, "text": "Official"}), \
                patch.object(c, "call", side_effect=[self.proposal, self.vote]) as call:
            r.run(self.root, reaudit=p["arxiv_id"])
        self.assertEqual(call.call_count, 2)
        ledger = r.read_json(self.root / "research/proposals.json")
        self.assertTrue(review.agreed(ledger["proposals"][p["arxiv_id"]], self.config))
        self.assertEqual(ledger["reaudits"][0]["status"], "held")
        self.assertIn("superseded_at", ledger["reaudits"][0])
        with self.assertRaisesRegex(ValueError, "held, rejected or needs_evidence"):
            r.run(self.root, reaudit=p["arxiv_id"])

    def test_reaudit_of_an_awaiting_candidate_resumes_from_saved_evidence(self):
        p = self.state["papers"][0]
        self.ledger["proposals"][p["arxiv_id"]] = {**self.proposal, "arxiv_id": p["arxiv_id"], "status": "awaiting_claude",
                                                   "claude_pending": {"source_run": "1", "context_sha256": "x"}}
        r.write_json(self.root / "research/proposals.json", self.ledger)
        r.save_state(self.root / "new-papers.json", self.state)
        with patch.object(c, "resume_one") as resume, patch.object(c, "unhold") as unhold, patch.object(r, "get_pdf") as pdf:
            r.run(self.root, reaudit=p["arxiv_id"])
        resume.assert_called_once()
        self.assertEqual(resume.call_args.args[4], p["arxiv_id"])
        unhold.assert_not_called()
        pdf.assert_not_called()

    def test_unusable_claude_answer_skips_only_that_paper(self):
        p = self.state["papers"][0]
        self.ledger["screenings"][p["arxiv_id"]] = {"status": "passed", "paper_title": p["title"], "abstract": p["summary"]}
        r.write_json(self.root / "research/proposals.json", self.ledger)
        r.save_state(self.root / "new-papers.json", self.state)
        with patch.object(r, "get_pdf", return_value=self.context["source"]), \
                patch.object(c, "call", side_effect=ValueError("Expecting value: line 1 column 1 (char 0)")):
            r.run(self.root)
        state = r.load_state(self.root / "new-papers.json")
        self.assertEqual(state["papers"][0]["analysis_status"], "needs_evidence")
        self.assertIn("Claude 응답 처리 실패", state["papers"][0]["analysis_reason"])
        self.assertEqual(state["research"]["status"], "ready")

    def test_abstract_screening_reuses_unchanged_result_without_pdf(self):
        r.write_json(self.root / "research/proposals.json", self.ledger)
        r.save_state(self.root / "new-papers.json", self.state)
        response = {"papers": {"2610.12345": {"decision": "irrelevant", "reason": "새 평가 자료 없음"}}}
        with patch.object(c, "call", return_value=response) as call, patch.object(r, "get_pdf") as pdf:
            r.run(self.root, screening_smoke=True)
            r.run(self.root, screening_smoke=True)
        call.assert_called_once()
        pdf.assert_not_called()
        record = r.read_json(self.root / "research/proposals.json")["screenings"]["2610.12345"]
        self.assertEqual(record["policy"], "claude_only")
        self.assertEqual(len(record["votes"]), 1)
        self.assertEqual(record["status"], "excluded")


if __name__ == "__main__":
    unittest.main()

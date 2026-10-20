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
        with patch.object(c, "call") as call, self.assertRaisesRegex(ValueError, "context hash"):
            c.resume_pending(self.root, self.ledger, self.state, self.config, time.monotonic() + 20)
        call.assert_not_called()

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


if __name__ == "__main__":
    unittest.main()

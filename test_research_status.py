"""Offline checks for the public research funnel and the daily summary."""
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

import build_research_status as status
from research_pipeline import read_json, write_json


class FakeGitHub:
    def __init__(self, issues=None, comments=None, label_exists=True):
        self.issues = issues or []
        self.comments = comments or []
        self.label_exists = label_exists
        self.calls = []

    def request(self, path, data=None, method=None):
        self.calls.append((path, data))
        if path.startswith("/labels/"):
            if self.label_exists:
                return {"name": status.LABEL}
            raise HTTPError(path, 404, "missing", {}, None)
        if path == "/labels":
            self.label_exists = True
            return data
        if path.startswith("/issues?"):
            return self.issues
        if path == "/issues":
            issue = {"number": 7, "html_url": "https://github.com/x/issues/7", **data}
            self.issues.append(issue)
            return issue
        if "/comments?" in path:
            return self.comments
        if path.endswith("/comments"):
            self.comments.append({"id": len(self.comments) + 1, "body": data["body"]})
            return {"html_url": "https://github.com/x/issues/7#issuecomment-1"}
        if path.startswith("/issues/comments/"):
            comment = next(c for c in self.comments if c["id"] == int(path.rsplit("/", 1)[1]))
            comment["body"] = data["body"]
            return {"html_url": f"https://github.com/x/issues/7#issuecomment-{comment['id']}"}
        raise AssertionError(path)


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

        def paper(key, **extra):
            return {"arxiv_id": key, "title": f"Paper {key}", "first_seen_at": "2026-10-20T00:00:00Z", **extra}
        papers = [
            paper("1", analysis_status="needs_evidence", analysis_reason="PDF 추출 실패(limit), 2026-10-29부터 재시도",
                  analysis_retry_after="2026-10-29", analysis_at="2026-10-22T03:00:00Z"),
            paper("2", analysis_status="needs_evidence", analysis_reason="Claude 응답 처리 실패, 다음 실행에서 재시도: Quote"),
            paper("3", analysis_status="exclude", analysis_reason="Claude 초록 선별에서 제외"),
            paper("4", analysis_status="queued"),
            paper("5", analysis_status="needs_evidence"),
            paper("6", analysis_status="exclude"),
            paper("7", analysis_status="accepted"),
            paper("8"),
            paper("9", analysis_status="needs_evidence", analysis_reason="공식 저장소 링크 없음(PDF에 GitHub·Hugging Face 주소가 없어 Claude 호출 생략), 2026-11-21부터 재시도",
                  analysis_retry_after="2026-11-21", analysis_at="2026-10-22T03:00:00Z"),
        ]
        write_json(self.root / "new-papers.json", {"schema_version": 1, "last_checked_at": "2026-10-22T02:00:00Z",
                                                   "research": {"last_run_at": "2026-10-22T03:00:00Z", "status": "ready"},
                                                   "papers": papers})
        write_json(self.root / "research/proposals.json", {"proposals": {
            "5": {"status": "needs_evidence", "reason": "링크 없음", "created_at": "2026-10-22T04:00:00Z"},
            "6": {"status": "exclude", "reason": "모델 논문", "created_at": "2026-10-21T04:00:00Z"},
            "7": {"status": "accepted", "reason": "반영", "created_at": "2026-10-22T05:00:00Z", "applied_at": "2026-10-22T06:00:00Z"}},
            "claude_daily_runs": {"2026-10-22": {"attempted": ["1", "2", "5", "6", "7", "9"], "abstract_attempted": ["4", "8"],
                                                 "calls": 9, "cost_usd": 3.4567}}})
        write_json(self.root / "updates.json", {"schema_version": 1, "updates": [
            {"arxiv_id": "7", "title": "Paper 7", "applied_at": "2026-10-22T06:00:00Z",
             "changes": [{"name": "Seven Bench", "action": "added", "inventory_url": "./english.html#inventory"}]}]})

    def test_every_paper_gets_a_stage_and_the_file_is_deterministic(self):
        result = status.build(self.root)
        stages = {p["arxiv_id"]: p["stage"] for p in result["papers"]}
        self.assertEqual(stages, {"1": "pdf_failed", "2": "draft_rejected", "3": "screened_out", "4": "queued",
                                  "5": "held", "6": "excluded", "7": "published", "8": "unscreened", "9": "link_missing"})
        seven = next(p for p in result["papers"] if p["arxiv_id"] == "7")
        self.assertEqual((seven["changes"], seven["inventory_url"]), (["Seven Bench"], "./english.html#inventory"))
        self.assertEqual(next(p for p in result["papers"] if p["arxiv_id"] == "1")["retry_after"], "2026-10-29")
        self.assertEqual(result["totals"]["papers"], 9)
        self.assertNotIn("generated_at", result)
        first = (self.root / status.OUTPUT).read_text()
        status.build(self.root)
        self.assertEqual(first, (self.root / status.OUTPUT).read_text())

    def test_day_counts_follow_the_attempt_list_and_applied_updates(self):
        result = status.build(self.root)
        day = result["days"][-1]
        self.assertEqual((day["day"], day["abstracts"], day["attempted"]), ("2026-10-22", 2, 6))
        counts = day["counts"]
        self.assertEqual((counts["pdf_failed"], counts["draft_rejected"], counts["held"], counts["published"]), (1, 1, 1, 1))
        # Paper 6 was concluded on 10-21 and only re-listed on 10-22.
        self.assertEqual(counts["carried"], 1)
        self.assertEqual(status.summary_line(result, "2026-10-22"),
                         "2026-10-22: 초록 선별 2건 · 본문 시도 6건 · PDF 실패 1건 · 링크 없음 1건 · 초안 거부 1건 · 제외 0건 · 보류 1건 · 검증 대기 0건 · 표 반영 1건 · 대기열 1건 · API 환산 비용 $3.46(Claude 호출 9회)")
        self.assertEqual((day["calls"], day["cost_usd"]), (9, 3.46))
        self.assertIn("실행 기록이 없습니다", status.summary_line(result, "2026-10-23"))

    def test_notify_creates_the_log_issue_once_and_never_repeats_a_day(self):
        result = status.build(self.root)
        github = FakeGitHub(label_exists=False)
        url = status.notify(github, result, "2026-10-22", "songys")
        self.assertTrue(url)
        self.assertTrue(any(path == "/labels" for path, _ in github.calls))
        self.assertEqual(github.issues[0]["labels"], [status.LABEL])
        body = github.comments[0]["body"]
        self.assertIn("<!-- research-log:2026-10-22 -->", body)
        self.assertIn("표 반영 1건", body)
        self.assertIn("[표의 행](https://lablup.github.io/llm-benchmark-inventory/english.html#inventory)", body)
        self.assertIn("근거 부족 보류 · [Paper 5](https://arxiv.org/abs/5)", body)
        again = FakeGitHub(issues=list(github.issues), comments=list(github.comments))
        self.assertIsNone(status.notify(again, result, "2026-10-22", "songys"))
        self.assertFalse(any(path.endswith("/comments") and data for path, data in again.calls))

    def test_a_later_run_on_the_same_day_rewrites_the_line_instead_of_adding_a_comment(self):
        result = status.build(self.root)
        github = FakeGitHub()
        status.notify(github, result, "2026-10-22", "songys")
        ledger = status.read_json(self.root / "research/proposals.json")
        ledger["claude_daily_runs"]["2026-10-22"]["attempted"].append("3")
        status.write_json(self.root / "research/proposals.json", ledger)
        later = status.build(self.root)
        url = status.notify(github, later, "2026-10-22", "songys")
        self.assertEqual(url, "https://github.com/x/issues/7#issuecomment-1")
        self.assertEqual(len(github.comments), 1)
        self.assertIn("본문 시도 7건", github.comments[0]["body"])
        self.assertTrue(any(path == "/issues/comments/1" for path, _ in github.calls))

    def test_titles_cannot_inject_markdown(self):
        self.assertEqual(status.markdown_title("[x](y) @me <b>"), "\\[x\\]\\(y\\) ＠me &lt;b&gt;")


if __name__ == "__main__":
    unittest.main()

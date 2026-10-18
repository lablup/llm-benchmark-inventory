"""Offline regression tests for discovery, recovery, and human review semantics."""
import copy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse
from xml.sax.saxutils import escape

import arxiv_watch as watch

NOW = datetime(2026, 10, 18, 1, 0, tzinfo=timezone.utc)


def empty():
    return {"schema_version": 1, "last_checked_at": None, "papers": []}


def paper(key="2610.12345", title="Example-Bench: A Benchmark for LLM Agents"):
    return {"arxiv_id": key, "title": title, "summary": "We introduce a benchmark for large language models.",
            "authors": ["Example Author"], "published": "2026-10-15T12:00:00Z", "updated": "2026-10-15T12:00:00Z",
            "categories": ["cs.CL"], "url": f"https://arxiv.org/abs/{key}", "first_seen_at": watch.iso(NOW),
            "review_status": "pending", "review_issue_url": None}


def feed(papers, total=None, start=0):
    entries = []
    for p in papers:
        fields = {"id": p["url"] + "v2", "title": p["title"], "summary": p["summary"],
                  "published": p["published"], "updated": p["updated"]}
        entries.append("<entry>" + "".join(f"<{key}>{escape(value)}</{key}>" for key, value in fields.items())
                       + '<author><name>Example Author</name></author><category term="cs.CL"/></entry>')
    return (f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:s="http://a9.com/-/spec/opensearch/1.1/">'
            f'<s:totalResults>{len(papers) if total is None else total}</s:totalResults>'
            f'<s:startIndex>{start}</s:startIndex>{"".join(entries)}</feed>').encode()


def issue(papers, checked=False, day="2026-10-18", author="github-actions[bot]"):
    body = watch.issue_body(papers, day, "songys")
    if checked:
        body = body.replace("- [ ]", "- [x]")
    return {"number": 7, "html_url": f"https://github.com/{watch.REPOSITORY}/issues/7",
            "body": body, "state": "open", "user": {"login": author}}


class CollectionTests(unittest.TestCase):
    def test_multiple_pages_and_version_ids(self):
        fetch = Mock(side_effect=[feed([paper()], total=2), feed([paper("2610.12346")], total=2, start=1)])
        sleep = Mock()
        result = watch.collect(empty(), NOW, fetch, sleep)
        self.assertEqual(len(result["papers"]), 2)
        self.assertEqual(result["last_checked_at"], watch.iso(NOW))
        sleep.assert_called_once_with(3)
        self.assertNotIn("v2", result["papers"][0]["arxiv_id"])

    def test_overlap_and_preserved_review(self):
        old = paper()
        old.update(review_status="reviewed", review_issue_url=issue([])["html_url"])
        state = {**empty(), "last_checked_at": "2026-10-17T01:00:00Z", "papers": [old, paper("2610.12346")]}
        revised = paper()
        revised.update(title="Revised Benchmark for LLMs", updated="2026-10-17T12:00:00Z")
        fetch = Mock(return_value=feed([revised]))
        result = watch.collect(state, NOW, fetch, Mock())
        kept = next(p for p in result["papers"] if p["arxiv_id"] == old["arxiv_id"])
        self.assertEqual(kept["title"], revised["title"])
        self.assertEqual(kept["review_status"], "reviewed")
        self.assertEqual(kept["review_issue_url"], old["review_issue_url"])
        self.assertEqual(len(result["papers"]), 2)
        self.assertIn("202610100100", parse_qs(urlparse(fetch.call_args.args[0]).query)["search_query"][0])
        self.assertEqual(state["papers"][0]["title"], old["title"])

    def test_partial_failure_does_not_advance_input(self):
        state = empty()
        fetch = Mock(side_effect=[feed([paper()], total=2), OSError("network unavailable")])
        with self.assertRaises(OSError):
            watch.collect(state, NOW, fetch, Mock())
        self.assertEqual(state, empty())

    def test_invalid_and_incomplete_results_fail(self):
        cases = [b"<html>unavailable</html>", feed([], total=1), feed([paper()], start=2),
                 feed([paper(), paper()], total=2), feed([paper()], total=5001)]
        for payload in cases:
            with self.subTest(payload=payload[:60]), self.assertRaises(ValueError):
                watch.collect(empty(), NOW, Mock(return_value=payload), Mock())

    def test_empty_day_retains_backlog(self):
        state = {**empty(), "papers": [paper()]}
        result = watch.collect(state, NOW, Mock(return_value=feed([])), Mock())
        self.assertEqual(result["papers"], state["papers"])

    def test_filter_rejects_unrelated_or_existing_benchmark_mentions(self):
        self.assertTrue(watch.candidate(paper()))
        self.assertTrue(watch.candidate(paper(title="A Dataset for Agent Evaluation")))
        self.assertFalse(watch.candidate(paper(title="A Faster Training Algorithm")))
        unrelated = paper(title="Benchmarking Solid State Batteries")
        unrelated["summary"] = "We present a new battery benchmark."
        self.assertFalse(watch.candidate(unrelated))

    def test_bad_url_or_review_status_rejected(self):
        for change in [{"url": "javascript:alert(1)"}, {"review_status": "approved"},
                       {"review_issue_url": "https://github.com/other/repo/issues/1"}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                watch.validate_state({**empty(), "papers": [{**paper(), **change}]})

    def test_atomic_state_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "papers.json"
            state = {**empty(), "papers": [paper()]}
            watch.save_state(path, state)
            self.assertEqual(watch.load_state(path), state)


class IssueTests(unittest.TestCase):
    def client(self, issues=()):
        client = Mock()
        client.issues.return_value = list(issues)
        client.request.return_value = issue([])
        return client

    def test_create_once_and_assign_reviewer(self):
        state = {**empty(), "papers": [paper()]}
        client = self.client()
        result = watch.sync_issues(state, client, NOW, "songys")
        self.assertEqual(client.request.call_args.args[1]["assignees"], ["songys"])
        self.assertEqual(result["papers"][0]["review_issue_url"], issue([])["html_url"])
        self.assertIsNone(state["papers"][0]["review_issue_url"])

    def test_recover_after_issue_creation_before_commit(self):
        state = {**empty(), "papers": [paper()]}
        client = self.client([issue(state["papers"])])
        result = watch.sync_issues(state, client, NOW + timedelta(days=1), "songys")
        client.request.assert_not_called()
        self.assertIsNotNone(result["papers"][0]["review_issue_url"])

    def test_checked_tasks_sync_even_when_issue_closed(self):
        state = {**empty(), "papers": [paper()]}
        reviewed = issue(state["papers"], checked=True)
        reviewed["state"] = "closed"
        result = watch.sync_issues(state, self.client([reviewed]), NOW, "songys")
        self.assertEqual(result["papers"][0]["review_status"], "reviewed")
        reviewed["body"] = reviewed["body"].replace("[x]", "[ ]")
        result = watch.sync_issues(result, self.client([reviewed]), NOW, "songys")
        self.assertEqual(result["papers"][0]["review_status"], "pending")

    def test_same_day_new_arrivals_wait_for_next_digest(self):
        state = {**empty(), "papers": [paper(), paper("2610.12346")]}
        client = self.client([issue([paper()])])
        result = watch.sync_issues(state, client, NOW, "songys")
        client.request.assert_not_called()
        self.assertIsNone(result["papers"][1]["review_issue_url"])

    def test_empty_queue_does_not_notify(self):
        client = self.client()
        watch.sync_issues(empty(), client, NOW, "songys")
        client.request.assert_not_called()

    def test_unauthorized_issue_cannot_clear_review(self):
        state = {**empty(), "papers": [paper()]}
        fake = issue(state["papers"], checked=True, author="untrusted-user")
        result = watch.sync_issues(state, self.client([fake]), NOW, "songys")
        self.assertEqual(result["papers"][0]["review_status"], "pending")

    def test_digest_limit_leaves_backlog_unlinked(self):
        state = {**empty(), "papers": [paper(f"2610.{i:05}") for i in range(102)]}
        result = watch.sync_issues(state, self.client(), NOW, "songys")
        self.assertEqual(sum(bool(p["review_issue_url"]) for p in result["papers"]), 100)

    def test_metadata_cannot_inject_tasks_mentions_or_links(self):
        malicious = paper(title="[bad](javascript:alert(1)) <img> @someone\n- [x] pretend")
        body = watch.issue_body([malicious], "2026-10-18", "songys")
        self.assertNotIn("@someone", body)
        self.assertNotIn("<img>", body)
        self.assertEqual(watch.TASK.findall(body), [(" ", malicious["arxiv_id"])])


if __name__ == "__main__":
    unittest.main()

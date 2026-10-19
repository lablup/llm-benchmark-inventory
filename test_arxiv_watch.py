"""Offline regression tests for discovery, recovery, and human review semantics."""
import copy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch
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
    body = "<!-- arxiv-review:v1:2026-10-18 -->"
    return {"number": 7, "html_url": f"https://github.com/{watch.REPOSITORY}/issues/7",
            "body": body, "state": "open", "user": {"login": author}}


class CollectionTests(unittest.TestCase):
    def test_multiple_pages_and_version_ids(self):
        fetch = Mock(side_effect=[feed([paper()], total=2), feed([paper("2610.12346")], total=2, start=1)])
        sleep = Mock()
        result = watch.collect(empty(), NOW, fetch, sleep)
        self.assertEqual(len(result["papers"]), 2)
        self.assertEqual(result["last_checked_at"], watch.iso(NOW))
        sleep.assert_called_once_with(10)
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


if __name__ == "__main__":
    unittest.main()


class CachedDiscoveryTests(unittest.TestCase):
    def test_transient_failure_keeps_checkpoint_and_candidates(self):
        state = {**empty(), "last_checked_at": watch.iso(NOW), "papers": [paper()]}
        original = copy.deepcopy(state)
        error = watch.HTTPError("https://export.arxiv.org", 429, "Limited", {}, None)
        self.addCleanup(error.close)
        with patch.object(watch, "collect", side_effect=error):
            result = watch.collect_with_cached_fallback(state, NOW)
        self.assertEqual(state, original)
        self.assertEqual(result["last_checked_at"], state["last_checked_at"])
        self.assertEqual(result["papers"], state["papers"])
        self.assertEqual(result["discovery_error"]["code"], "HTTP 429")

    def test_schema_errors_still_stop_collection(self):
        with patch.object(watch, "collect", side_effect=ValueError("Incomplete page")):
            with self.assertRaises(ValueError):
                watch.collect_with_cached_fallback(empty(), NOW)

    def test_success_clears_previous_failure(self):
        state = {**empty(), "discovery_error": {"code": "HTTP 429"}}
        with patch.object(watch, "collect", return_value=copy.deepcopy(state)):
            self.assertNotIn("discovery_error", watch.collect_with_cached_fallback(state, NOW))


class RequestPacingTests(unittest.TestCase):
    def test_retry_after_seconds_date_and_fallback(self):
        self.assertEqual(watch.retry_delay({}, 0), 60)
        self.assertEqual(watch.retry_delay({}, 1), 120)
        self.assertEqual(watch.retry_delay({}, 2), 240)
        self.assertEqual(watch.retry_delay({"Retry-After": "600"}, 0), 600)
        self.assertEqual(watch.retry_delay({"Retry-After": "Sun, 18 Oct 2026 01:05:00 GMT"}, 0, NOW), 300)
        self.assertEqual(watch.retry_delay({"Retry-After": "invalid"}, 0), 60)

    def test_long_cooldown_does_not_retry_early(self):
        error = watch.HTTPError("https://export.arxiv.org", 429, "Limited", {"Retry-After": "600"}, None)
        self.addCleanup(error.close)
        with patch.object(watch, "urlopen", side_effect=error) as request, patch.object(watch.time, "sleep") as sleep:
            result = watch.collect_with_cached_fallback(empty(), NOW)
        self.assertEqual(request.call_count, 1)
        sleep.assert_not_called()
        self.assertIn("retry_at", result["discovery_error"])
        with patch.object(watch, "collect") as collect:
            watch.collect_with_cached_fallback(result, NOW)
        collect.assert_not_called()

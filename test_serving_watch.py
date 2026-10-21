"""Serving watcher: change detection per source kind, resilience and notifications."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import serving_watch as w

NOW = datetime(2026, 10, 22, 2, 30, tzinfo=timezone.utc)


def responses(table):
    def get(url):
        value = table[url]
        if isinstance(value, Exception):
            raise value
        return json.dumps(value).encode() if not isinstance(value, bytes) else value
    return get


class ServingWatchTests(unittest.TestCase):
    def setUp(self):
        self.state = w.load_state(Path(tempfile.mkdtemp()) / "missing.json")

    def test_sources_file_is_valid_and_names_inventory_rows(self):
        sources = w.load_sources()
        self.assertTrue(sources)
        self.assertEqual({s["id"] for s in sources} - w.inventory_ids(), set())
        self.assertEqual(len({w.source_key(s) for s in sources}), len(sources))

    def test_release_baseline_then_change(self):
        source = {"id": "all-smi", "kind": "github_release", "repo": "lablup/all-smi"}
        url = "https://api.github.com/repos/lablup/all-smi/releases/latest"
        first = w.check([source], self.state, NOW, responses({url: {"tag_name": "v0.28.1", "published_at": "2026-10-20T02:26:12Z", "html_url": "https://github.com/lablup/all-smi/releases/tag/v0.28.1", "name": "v0.28.1"}}))
        self.assertEqual(first, [])
        second = w.check([source], self.state, NOW, responses({url: {"tag_name": "v0.29.0", "published_at": "2026-10-22T00:00:00Z", "html_url": "https://github.com/lablup/all-smi/releases/tag/v0.29.0", "name": "v0.29.0"}}))
        self.assertEqual([(c["before"], c["after"], c["kind"]) for c in second], [("v0.28.1", "v0.29.0", "github_release")])
        record = self.state["sources"][w.source_key(source)]
        self.assertEqual(record["observed"]["value"], "v0.29.0")
        self.assertEqual(record["history"][0]["value"], "v0.28.1")
        self.assertIsNone(second[0]["notified"])

    def test_commits_org_repos_and_pypi_observations(self):
        commits = {"id": "genai-perf", "kind": "github_commits", "repo": "t/p", "path": "genai-perf"}
        org = {"id": "mlperf-inference", "kind": "github_org_repos", "org": "mlcommons", "pattern": "^inference_results_v"}
        pypi = {"id": "aiperf", "kind": "pypi", "package": "aiperf"}
        get = responses({
            "https://api.github.com/repos/t/p/commits?per_page=1&path=genai-perf": [{"sha": "abcdef0123456789", "html_url": "https://github.com/t/p/commit/abc", "commit": {"committer": {"date": "2026-09-15T23:03:23Z"}, "message": "Fix\n\nbody"}}],
            "https://api.github.com/orgs/mlcommons/repos?per_page=100&sort=created&direction=desc": [
                {"name": "inference_results_v5.1", "created_at": "2025-09-01T00:00:00Z", "html_url": "https://github.com/mlcommons/inference_results_v5.1"},
                {"name": "endpoints_results", "created_at": "2026-10-01T00:00:00Z", "html_url": "x"},
                {"name": "inference_results_v6.1", "created_at": "2026-10-10T00:00:00Z", "html_url": "https://github.com/mlcommons/inference_results_v6.1"}],
            "https://pypi.org/pypi/aiperf/json": {"info": {"version": "0.13.0", "summary": "Perf"}, "releases": {"0.13.0": [{"upload_time_iso_8601": "2026-10-20T20:29:11Z"}]}},
        })
        w.check([commits, org, pypi], self.state, NOW, get)
        observed = {key: record["observed"]["value"] for key, record in self.state["sources"].items()}
        self.assertEqual(observed[w.source_key(commits)], "abcdef012345")
        self.assertEqual(observed[w.source_key(org)], "inference_results_v6.1")
        self.assertEqual(observed[w.source_key(pypi)], "0.13.0")
        self.assertEqual(self.state["sources"][w.source_key(commits)]["observed"]["detail"], "Fix")

    def test_page_hash_ignores_scripts_and_whitespace_and_rejects_error_pages(self):
        body = "<html><body><h1>Endpoints</h1><p>" + "Result row. " * 40 + "</p></body></html>"
        noisy = body.replace("<h1>", "<script>var nonce='abc'</script>\n\n<style>.x{}</style><h1>")
        self.assertEqual(w.page_text(body.encode()), w.page_text(noisy.encode()))
        source = {"id": "mlperf-endpoints", "kind": "page", "url": "https://mlcommons.org/benchmarks/endpoints/"}
        w.check([source], self.state, NOW, responses({source["url"]: body.encode()}))
        self.assertEqual(w.check([source], self.state, NOW, responses({source["url"]: noisy.encode()})), [])
        changed = w.check([source], self.state, NOW, responses({source["url"]: body.replace("Result row.", "New row.").encode()}))
        self.assertEqual(len(changed), 1)
        w.check([source], self.state, NOW, responses({source["url"]: b"<html>error</html>"}))
        record = self.state["sources"][w.source_key(source)]
        self.assertIn("too short", record["error"]["message"])
        self.assertEqual(record["observed"]["value"], changed[0]["after"])

    def test_unavailable_source_keeps_previous_observation_and_continues(self):
        a = {"id": "guidellm", "kind": "pypi", "package": "guidellm"}
        b = {"id": "all-smi", "kind": "github_release", "repo": "lablup/all-smi"}
        ok = {"https://pypi.org/pypi/guidellm/json": {"info": {"version": "0.8.1"}, "releases": {"0.8.1": []}},
              "https://api.github.com/repos/lablup/all-smi/releases/latest": {"tag_name": "v1", "html_url": "https://github.com/lablup/all-smi/releases/tag/v1"}}
        w.check([a, b], self.state, NOW, responses(ok))
        broken = dict(ok, **{"https://pypi.org/pypi/guidellm/json": OSError("boom")})
        found = w.check([a, b], self.state, NOW, responses(broken))
        self.assertEqual(found, [])
        self.assertEqual(self.state["sources"][w.source_key(a)]["observed"]["value"], "0.8.1")
        self.assertIn("OSError", self.state["sources"][w.source_key(a)]["error"]["message"])
        self.assertIsNone(self.state["sources"][w.source_key(b)]["error"])

    def test_notify_opens_one_issue_and_marks_changes(self):
        self.state["changes"] = [
            {"detected_at": w.iso(NOW), "serving_id": "all-smi", "kind": "github_release", "source": "k", "before": "v0.28.1", "after": "v0.29.0", "date": "2026-10-22T00:00:00Z", "url": "https://github.com/lablup/all-smi/releases/tag/v0.29.0", "detail": "v0.29.0 <b>", "notified": None},
            {"detected_at": w.iso(NOW), "serving_id": "mlperf-endpoints", "kind": "page", "source": "k2", "before": "aaaa", "after": "bbbb", "date": None, "url": "https://mlcommons.org/benchmarks/endpoints/", "detail": None, "notified": "https://github.com/x/issues/1"}]
        github = Mock()
        github.request.return_value = {"html_url": "https://github.com/lablup/llm-benchmark-inventory/issues/99"}
        issue = w.notify(self.state, github, NOW, "songys", {"all-smi": "Lablup all-smi"})
        github.ensure_label.assert_called_once()
        payload = github.request.call_args.args[1]
        self.assertEqual(payload["title"], "[서빙 감시] 2026-10-22 · 변경 1건")
        self.assertEqual(payload["assignees"], ["songys"])
        self.assertIn("## Lablup all-smi (`all-smi`)", payload["body"])
        self.assertIn("`v0.28.1` → `v0.29.0`", payload["body"])
        self.assertIn("&lt;b&gt;", payload["body"])
        self.assertIn("자동으로 바뀌지 않습니다", payload["body"])
        self.assertEqual(self.state["changes"][0]["notified"], issue["html_url"])
        self.assertIsNone(w.notify(self.state, github, NOW, "songys", {}))

    def test_state_round_trip_and_validation(self):
        path = Path(tempfile.mkdtemp()) / "serving-watch.json"
        w.save_state(self.state, path)
        self.assertEqual(w.load_state(path)["schema_version"], 1)
        with self.assertRaises(ValueError):
            w.validate_state({"schema_version": 2})


if __name__ == "__main__":
    unittest.main()

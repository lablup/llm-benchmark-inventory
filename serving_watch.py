#!/usr/bin/env python3
"""Watch serving tools, public boards and resource monitors for new releases or updates.

Sources are listed by hand in serving-watch-sources.json, one or more per row of
serving_inventory.csv. Each daily run records what it observed in serving-watch.json
and, with --notify, opens one GitHub issue listing the changes since the last run.
The watcher never edits serving_inventory.csv or the reference values: a person
reads the issue, checks the source and updates the table (DECISIONS.md 20).

Source kinds (the observed value is the thing compared between runs):
  github_release   latest release tag of a repository
  github_commits   latest commit on the default branch, optionally for one path
  github_org_repos newest repository of an organization whose name matches a pattern
  pypi             latest version on PyPI
  page             sha256 of a web page's visible text (scripts, styles and tags removed)

Standard library only. GH_TOKEN raises the GitHub API limit and is required for --notify.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from arxiv_watch import ROOT, KST, iso, markdown_title

SOURCES_PATH = ROOT / "serving-watch-sources.json"
STATE_PATH = ROOT / "serving-watch.json"
INVENTORY_PATH = ROOT / "serving_inventory.csv"
REPOSITORY = "lablup/llm-benchmark-inventory"
LABEL = "serving-watch"
KINDS = {"github_release", "github_commits", "github_org_repos", "pypi", "page"}
HISTORY_LIMIT = 20
USER_AGENT = "llm-benchmark-inventory serving-watch/1.0"
KIND_LABEL = {"github_release": "새 릴리스", "github_commits": "새 커밋", "github_org_repos": "새 저장소",
              "pypi": "PyPI 새 버전", "page": "페이지 내용 변경"}


def source_key(source: dict) -> str:
    target = source.get("repo") or source.get("package") or source.get("org") or source.get("url")
    path = source.get("path") or source.get("pattern") or ""
    return f"{source['id']}:{source['kind']}:{target}" + (f"#{path}" if path else "")


def load_sources(path: Path = SOURCES_PATH) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("sources"), list):
        raise ValueError("Invalid serving watch sources")
    keys = set()
    for source in data["sources"]:
        if source.get("kind") not in KINDS or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", source.get("id", "")):
            raise ValueError(f"Invalid serving watch source: {source}")
        need = {"github_release": "repo", "github_commits": "repo", "github_org_repos": "org", "pypi": "package", "page": "url"}[source["kind"]]
        if not isinstance(source.get(need), str) or not source[need]:
            raise ValueError(f"Serving watch source needs {need}: {source}")
        if "repo" in source and not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source["repo"]):
            raise ValueError(f"Invalid repository: {source['repo']}")
        if source["kind"] == "page" and urlsplit(source["url"]).scheme != "https":
            raise ValueError(f"Page sources must be https: {source['url']}")
        key = source_key(source)
        if key in keys:
            raise ValueError(f"Duplicate serving watch source: {key}")
        keys.add(key)
    return data["sources"]


def inventory_ids(path: Path = INVENTORY_PATH) -> set[str]:
    import csv
    with path.open(encoding="utf-8-sig", newline="") as file:
        return {row["id"] for row in csv.DictReader(file)}


def load_state(path: Path = STATE_PATH) -> dict:
    if not path.exists():
        return {"schema_version": 1, "checked_at": None, "sources": {}, "changes": []}
    state = json.loads(path.read_text(encoding="utf-8"))
    validate_state(state)
    return state


def validate_state(state: dict) -> None:
    if state.get("schema_version") != 1 or not isinstance(state.get("sources"), dict) or not isinstance(state.get("changes"), list):
        raise ValueError("Invalid serving watch state")
    for key, record in state["sources"].items():
        if not isinstance(record, dict) or not isinstance(record.get("history", []), list):
            raise ValueError(f"Invalid serving watch record: {key}")
    for change in state["changes"]:
        if not {"detected_at", "serving_id", "kind", "before", "after"} <= set(change):
            raise ValueError("Invalid serving watch change")


def save_state(state: dict, path: Path = STATE_PATH) -> None:
    validate_state(state)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch(url: str, token: str | None = None, limit: int = 2_000_000) -> bytes:
    """Plain GET with redirects allowed; the result is data, never instructions."""
    headers = {"User-Agent": USER_AGENT}
    if urlsplit(url).hostname == "api.github.com":
        headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        if token:
            headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=45) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Response too large")
    return data


def page_text(html: bytes) -> str:
    text = html.decode("utf-8", "replace")
    text = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def observe(source: dict, get) -> dict:
    """Return {"value", "date", "url", "detail"} for one source. `get(url)` returns bytes."""
    kind = source["kind"]
    if kind == "github_release":
        data = json.loads(get(f"https://api.github.com/repos/{source['repo']}/releases/latest"))
        return {"value": data["tag_name"], "date": data.get("published_at"), "url": data.get("html_url"),
                "detail": (data.get("name") or "")[:120]}
    if kind == "github_commits":
        path = f"&path={quote(source['path'])}" if source.get("path") else ""
        data = json.loads(get(f"https://api.github.com/repos/{source['repo']}/commits?per_page=1{path}"))
        if not data:
            raise ValueError("No commits returned")
        commit = data[0]
        return {"value": commit["sha"][:12], "date": commit["commit"]["committer"]["date"], "url": commit.get("html_url"),
                "detail": commit["commit"]["message"].splitlines()[0][:120]}
    if kind == "github_org_repos":
        data = json.loads(get(f"https://api.github.com/orgs/{source['org']}/repos?per_page=100&sort=created&direction=desc"))
        pattern = re.compile(source.get("pattern", ""))
        matches = sorted((repo for repo in data if pattern.search(repo["name"])), key=lambda repo: repo["created_at"], reverse=True)
        if not matches:
            raise ValueError("No repository matches the pattern")
        newest = matches[0]
        return {"value": newest["name"], "date": newest["created_at"], "url": newest.get("html_url"),
                "detail": f"{len(matches)} matching repositories"}
    if kind == "pypi":
        data = json.loads(get(f"https://pypi.org/pypi/{quote(source['package'])}/json"))
        version = data["info"]["version"]
        uploads = [file.get("upload_time_iso_8601") or file.get("upload_time") for file in data["releases"].get(version, [])]
        return {"value": version, "date": max(uploads) if uploads else None,
                "url": f"https://pypi.org/project/{source['package']}/{version}/", "detail": (data["info"].get("summary") or "")[:120]}
    if kind == "page":
        text = page_text(get(source["url"]))
        if len(text) < 200:
            raise ValueError(f"Page text too short ({len(text)} chars); probably an error page")
        return {"value": hashlib.sha256(text.encode()).hexdigest()[:16], "date": None, "url": source["url"],
                "detail": f"{len(text)} chars of visible text"}
    raise ValueError(f"Unsupported source kind: {kind}")


def check(sources: list[dict], state: dict, now: datetime, get) -> list[dict]:
    """Observe every source, record changes since the previous observation, return the new changes."""
    found = []
    for source in sources:
        key = source_key(source)
        record = state["sources"].setdefault(key, {"serving_id": source["id"], "kind": source["kind"], "observed": None,
                                                   "observed_at": None, "error": None, "history": []})
        record.update(serving_id=source["id"], kind=source["kind"], note=source.get("note"))
        try:
            observation = observe(source, get)
        except (HTTPError, URLError, ValueError, KeyError, TimeoutError, OSError) as error:
            record["error"] = {"at": iso(now), "message": f"{type(error).__name__}: {str(error)[:200]}"}
            print(f"{key}: unavailable, keeping the previous observation ({record['error']['message']})", flush=True)
            continue
        record["error"] = None
        previous = record.get("observed")
        if previous is None:
            print(f"{key}: baseline {observation['value']}", flush=True)
        elif previous["value"] != observation["value"]:
            change = {"detected_at": iso(now), "serving_id": source["id"], "kind": source["kind"], "source": key,
                      "before": previous["value"], "after": observation["value"], "date": observation.get("date"),
                      "url": observation.get("url"), "detail": observation.get("detail"), "notified": None}
            state["changes"].append(change)
            found.append(change)
            record["history"] = ([previous] + record.get("history", []))[:HISTORY_LIMIT]
            print(f"{key}: {previous['value']} -> {observation['value']}", flush=True)
        record["observed"] = observation
        record["observed_at"] = iso(now)
    state["checked_at"] = iso(now)
    return found


def issue_body(changes: list[dict], names: dict[str, str], day: str) -> str:
    lines = [f"<!-- serving-watch:v1:{day} -->",
             "서빙·자원 인벤토리가 가리키는 도구·보드에서 지난 확인 이후 바뀐 것을 모았습니다.",
             "표(`serving_inventory.csv`, 대표 측정값)는 자동으로 바뀌지 않습니다. 출처를 열어 확인한 뒤 필요한 행과 `최근 확인일`을 손으로 갱신해 주세요.", ""]
    by_row: dict[str, list[dict]] = {}
    for change in changes:
        by_row.setdefault(change["serving_id"], []).append(change)
    for serving_id, items in by_row.items():
        lines.append(f"## {markdown_title(names.get(serving_id, serving_id))} (`{serving_id}`)")
        for change in items:
            label = KIND_LABEL.get(change["kind"], change["kind"])
            when = f" · {change['date'][:10]}" if change.get("date") else ""
            link = f" · [출처]({change['url']})" if change.get("url", "").startswith("https://") else ""
            detail = f" — {markdown_title(change['detail'], 120)}" if change.get("detail") else ""
            if change["kind"] == "page":
                lines.append(f"- {label}{when}{link}: 보이는 본문의 해시가 `{change['before']}`에서 `{change['after']}`로 바뀜{detail}")
            else:
                lines.append(f"- {label}{when}{link}: `{markdown_title(change['before'], 60)}` → `{markdown_title(change['after'], 60)}`{detail}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


class GitHub:
    def __init__(self, token: str):
        if not token:
            raise ValueError("GH_TOKEN is required for notifications")
        self.token = token

    def request(self, path: str, data=None, method=None):
        request = Request("https://api.github.com/repos/" + REPOSITORY + path,
                          data=json.dumps(data).encode() if data is not None else None, method=method,
                          headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": USER_AGENT})
        with urlopen(request, timeout=45) as response:
            return json.load(response)

    def ensure_label(self) -> None:
        try:
            self.request(f"/labels/{LABEL}")
        except HTTPError as error:
            if error.code != 404:
                raise
            self.request("/labels", {"name": LABEL, "color": "0e8a16",
                                     "description": "Serving tool, board and monitor updates awaiting a manual table review"})


def notify(state: dict, github: GitHub, now: datetime, reviewer: str, names: dict[str, str]) -> dict | None:
    pending = [change for change in state["changes"] if not change.get("notified")]
    if not pending:
        return None
    day = now.astimezone(KST).date().isoformat()
    github.ensure_label()
    issue = github.request("/issues", {"title": f"[서빙 감시] {day} · 변경 {len(pending)}건",
                                       "body": issue_body(pending, names, day), "labels": [LABEL], "assignees": [reviewer]})
    for change in pending:
        change["notified"] = issue["html_url"]
    return issue


def serving_names(path: Path = INVENTORY_PATH) -> dict[str, str]:
    import csv
    with path.open(encoding="utf-8-sig", newline="") as file:
        return {row["id"]: row["이름"] for row in csv.DictReader(file)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources", type=Path, default=SOURCES_PATH)
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    parser.add_argument("--notify", action="store_true", help="Open one GitHub issue for changes not yet announced")
    parser.add_argument("--reviewer", default=os.environ.get("ARXIV_REVIEWER", "songys"))
    parser.add_argument("--dry-run", action="store_true", help="Observe and print, but save nothing")
    args = parser.parse_args()
    sources = load_sources(args.sources)
    unknown = {source["id"] for source in sources} - inventory_ids()
    if unknown:
        raise SystemExit(f"serving-watch-sources.json names rows missing from serving_inventory.csv: {sorted(unknown)}")
    state = load_state(args.state)
    now = datetime.now(timezone.utc)
    token = os.environ.get("GH_TOKEN")
    found = check(sources, state, now, lambda url: fetch(url, token))
    errors = [key for key, record in state["sources"].items() if record.get("error")]
    print(f"serving watch: {len(sources)} sources, {len(found)} changes, {len(errors)} unavailable", flush=True)
    if args.dry_run:
        return 0
    if args.notify:
        issue = notify(state, GitHub(token), now, args.reviewer, serving_names())
        if issue:
            print(f"notified: {issue['html_url']}", flush=True)
    save_state(state, args.state)
    return 0


if __name__ == "__main__":
    sys.exit(main())

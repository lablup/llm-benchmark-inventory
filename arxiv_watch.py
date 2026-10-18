#!/usr/bin/env python3
"""Discover arXiv candidates; notify only after evidence-backed proposals exist.

Standard library only. Discovery never changes the curated inventory CSVs.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "new-papers.json"
REPOSITORY = "lablup/llm-benchmark-inventory"
SITE = "https://lablup.github.io/llm-benchmark-inventory/papers.html"
LABEL = "arxiv-review"
ATOM = "{http://www.w3.org/2005/Atom}"
SEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"
ARXIV_ID = r"\d{4}\.\d{4,5}"
TOPIC_QUERY = (
    '(ti:benchmark OR ti:bench OR ti:evaluation OR ti:dataset) AND '
    '(all:"language model" OR all:LLM OR all:LLMs OR all:VLM OR '
    'all:"vision language" OR all:"multimodal model")'
)
MODEL = re.compile(r"\b(?:LLMs?|VLMs?|(?:large |vision[- ]|multimodal )?language models?|multimodal models?)\b", re.I)
BENCH = re.compile(r"bench(?:mark(?:ing|s)?)?\b", re.I)
INTRODUCES = re.compile(r"\b(?:introduc\w*|propos\w*|present\w*|releas\w*|construct\w*)\b", re.I)
KST = timezone(timedelta(hours=9))


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed


def iso(now: datetime) -> str:
    return now.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_state(path: Path) -> dict:
    state = json.loads(path.read_text(encoding="utf-8"))
    validate_state(state)
    return state


def validate_state(state: dict) -> None:
    if state.get("schema_version") != 1 or not isinstance(state.get("papers"), list):
        raise ValueError("Unsupported paper state")
    if state.get("last_checked_at"):
        timestamp(state["last_checked_at"])
    ids = set()
    for paper in state["papers"]:
        key = paper["arxiv_id"]
        if not re.fullmatch(ARXIV_ID, key) or key in ids:
            raise ValueError(f"Invalid or duplicate arXiv ID: {key}")
        ids.add(key)
        if paper["url"] != f"https://arxiv.org/abs/{key}":
            raise ValueError("Invalid arXiv URL")
        if paper["review_status"] not in {"pending", "reviewed"}:
            raise ValueError("Invalid review status")
        if paper.get("analysis_status", "queued") not in {"queued", "proposed", "accepted", "held", "rejected", "exclude", "needs_evidence"}:
            raise ValueError("Invalid analysis status")
        issue = paper.get("review_issue_url")
        if issue and not re.fullmatch(r"https://github\.com/" + re.escape(REPOSITORY) + r"/issues/\d+", issue):
            raise ValueError("Invalid review issue URL")
        for field in ("title", "summary"):
            if not isinstance(paper[field], str) or not paper[field].strip():
                raise ValueError(f"Missing {field}")
        for field in ("published", "updated", "first_seen_at"):
            timestamp(paper[field])
        for field in ("authors", "categories"):
            if not isinstance(paper[field], list) or not all(isinstance(x, str) for x in paper[field]):
                raise ValueError(f"Invalid {field}")


def save_state(path: Path, state: dict) -> None:
    validate_state(state)
    text = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def parse_feed(payload: bytes, expected_start: int) -> tuple[int, list[dict]]:
    root = ET.fromstring(payload)
    if root.tag != ATOM + "feed":
        raise ValueError("arXiv did not return an Atom feed")
    total = int(root.findtext(SEARCH + "totalResults", "-1"))
    start = int(root.findtext(SEARCH + "startIndex", "-1"))
    if total < 0 or start != expected_start:
        raise ValueError("arXiv returned invalid pagination or an error feed")
    papers = []
    for entry in root.findall(ATOM + "entry"):
        raw_id = entry.findtext(ATOM + "id", "")
        match = re.fullmatch(r"https?://arxiv\.org/abs/(" + ARXIV_ID + r")(?:v\d+)?", raw_id)
        if not match:
            raise ValueError(f"Invalid arXiv entry: {raw_id}")
        key = match[1]
        paper = {
            "arxiv_id": key,
            "title": " ".join(entry.findtext(ATOM + "title", "").split()),
            "summary": " ".join(entry.findtext(ATOM + "summary", "").split()),
            "authors": [" ".join(author.findtext(ATOM + "name", "").split()) for author in entry.findall(ATOM + "author")],
            "published": entry.findtext(ATOM + "published", ""),
            "updated": entry.findtext(ATOM + "updated", ""),
            "categories": [category.attrib["term"] for category in entry.findall(ATOM + "category")],
            "url": f"https://arxiv.org/abs/{key}",
        }
        timestamp(paper["published"])
        timestamp(paper["updated"])
        if not paper["title"] or not paper["summary"]:
            raise ValueError("arXiv entry is missing title or abstract")
        papers.append(paper)
    return total, papers


def candidate(paper: dict) -> bool:
    """Conservative discovery heuristic, not a claim of inventory eligibility."""
    title, summary = paper["title"], paper["summary"]
    if not MODEL.search(title + " " + summary):
        return False
    return bool(BENCH.search(title) or (
        re.search(r"\b(?:evaluation|dataset)\b", title, re.I)
        and BENCH.search(summary) and INTRODUCES.search(summary)
    ))


def fetch_url(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": f"llm-benchmark-inventory/1.0 (https://github.com/{REPOSITORY})"})
    for attempt in range(4):
        try:
            with urlopen(request, timeout=45) as response:
                return response.read()
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 3:
                raise
        except (URLError, TimeoutError):
            if attempt == 3:
                raise
        time.sleep(3 * (2 ** attempt))
    raise RuntimeError("arXiv request failed")


def collect(state: dict, now: datetime, fetch=fetch_url, sleep=time.sleep) -> dict:
    """Fetch every page before advancing the checkpoint; retain older review data."""
    since = timestamp(state["last_checked_at"]) - timedelta(days=7) if state.get("last_checked_at") else now - timedelta(days=30)
    since = since.astimezone(timezone.utc).replace(second=0, microsecond=0)
    if since > now:
        raise ValueError("Collection checkpoint is in the future")
    query = f"({TOPIC_QUERY}) AND submittedDate:[{since:%Y%m%d%H%M} TO {now:%Y%m%d%H%M}]"
    found: dict[str, dict] = {}
    start = 0
    while True:
        url = "https://export.arxiv.org/api/query?" + urlencode({
            "search_query": query, "start": start, "max_results": 100,
            "sortBy": "submittedDate", "sortOrder": "descending",
        })
        total, page = parse_feed(fetch(url), start)
        if total > 5000:
            raise ValueError("More than 5000 results; narrow the query before advancing the checkpoint")
        if not page and start < total:
            raise ValueError("arXiv returned an incomplete page; checkpoint was not advanced")
        for paper in page:
            if not since <= timestamp(paper["published"]) <= now:
                raise ValueError("arXiv returned a paper outside the requested date range")
            previous = found.get(paper["arxiv_id"])
            if previous is None or timestamp(paper["updated"]) > timestamp(previous["updated"]):
                found[paper["arxiv_id"]] = paper
        start += len(page)
        if start >= total:
            break
        sleep(3)
    if len(found) != total:
        raise ValueError("arXiv pagination changed during collection; retry without advancing the checkpoint")
    result = copy.deepcopy(state)
    by_id = {p["arxiv_id"]: p for p in result["papers"]}
    for key, paper in found.items():
        if key in by_id:
            if timestamp(paper["updated"]) >= timestamp(by_id[key]["updated"]):
                by_id[key].update(paper)
        elif candidate(paper):
            by_id[key] = {**paper, "first_seen_at": iso(now), "review_status": "pending", "review_issue_url": None}
    result["papers"] = sorted(by_id.values(), key=lambda p: (p["published"], p["arxiv_id"]), reverse=True)
    result["last_checked_at"] = iso(now)
    validate_state(result)
    return result


class GitHub:
    def __init__(self, token: str):
        if not token:
            raise ValueError("GH_TOKEN is required for issue synchronization")
        self.token = token

    def request(self, path: str, data=None):
        request = Request("https://api.github.com/repos/" + REPOSITORY + path,
                          data=json.dumps(data).encode() if data is not None else None,
                          headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "llm-benchmark-inventory"})
        with urlopen(request, timeout=45) as response:
            return json.load(response)

    def issues(self) -> list[dict]:
        issues = []
        page = 1
        while True:
            batch = self.request(f"/issues?state=all&labels={LABEL}&per_page=100&page={page}")
            issues.extend(issue for issue in batch if "pull_request" not in issue)
            if len(batch) < 100:
                return issues
            page += 1

    def ensure_label(self) -> None:
        try:
            self.request(f"/labels/{LABEL}")
        except HTTPError as error:
            if error.code != 404:
                raise
            self.request("/labels", {"name": LABEL, "color": "1976e8", "description": "Evidence-backed inventory changes awaiting approval"})


def markdown_title(title: str, limit: int = 300) -> str:
    # Prevent metadata from injecting Markdown links, HTML, or @mentions.
    title = " ".join(title.split()).replace("@", "＠").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", title[:limit])


def sync_issues(state: dict, github: GitHub, now: datetime, reviewer: str) -> dict:
    # Kept as the collector's public entry point; v1 raw-paper digests are retired.
    from review_proposals import sync
    return sync(state, github, now, reviewer)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    parser.add_argument("--github", action="store_true", help="Create and sync daily review issues")
    parser.add_argument("--issues-only", action="store_true", help="Sync reviews without querying arXiv")
    parser.add_argument("--reviewer", default=os.environ.get("ARXIV_REVIEWER", "songys"))
    args = parser.parse_args()
    if args.issues_only and not args.github:
        parser.error("--issues-only requires --github")
    now = datetime.now(timezone.utc)
    state = load_state(args.state)
    before = len(state["papers"])
    if not args.issues_only:
        state = collect(state, now)
        # Preserve discovery even if GitHub is temporarily unavailable.
        save_state(args.state, state)
    if args.github:
        state = sync_issues(state, GitHub(os.environ.get("GH_TOKEN", "")), now, args.reviewer)
        save_state(args.state, state)
    print(f"Papers: {len(state['papers'])}; new: {len(state['papers']) - before}; proposals: {sum(p.get('analysis_status') == 'proposed' for p in state['papers'])}")


if __name__ == "__main__":
    main()

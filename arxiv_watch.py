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
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "new-papers.json"
REPOSITORY = "lablup/llm-benchmark-inventory"
SITE = "https://lablup.github.io/llm-benchmark-inventory/papers.html"
LABEL = "arxiv-review"
OAI = "{http://www.openarchives.org/OAI/2.0/}"
OAI_ARXIV = "{http://arxiv.org/OAI/arXiv/}"
RSS_ARXIV = "{http://arxiv.org/schemas/atom}"
DC = "{http://purl.org/dc/elements/1.1/}"
ARXIV_ID = r"\d{4}\.\d{4,5}"
RSS_FEEDS = ("cs", "econ", "eess", "math", "physics", "q-bio", "q-fin", "stat")
OAI_URL = "https://oaipmh.arxiv.org/oai"
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
        timestamp(paper["first_seen_at"])
        for field in ("published", "updated", "announced_at", "metadata_changed_at"):
            if paper.get(field):
                timestamp(paper[field])
        if not paper.get("published") and not paper.get("announced_at"):
            raise ValueError("Paper needs a submission or announcement date")
        for field in ("authors", "categories"):
            if not isinstance(paper[field], list) or not all(isinstance(x, str) for x in paper[field]):
                raise ValueError(f"Invalid {field}")


def save_state(path: Path, state: dict) -> None:
    validate_state(state)
    text = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def candidate(paper: dict) -> bool:
    """Conservative discovery heuristic, not a claim of inventory eligibility."""
    title, summary = paper["title"], paper["summary"]
    if not MODEL.search(title + " " + summary):
        return False
    return bool(BENCH.search(title) or (
        re.search(r"\b(?:evaluation|dataset)\b", title, re.I)
        and BENCH.search(summary) and INTRODUCES.search(summary)
    ))


def retry_delay(headers, attempt, now=None):
    """Honor Retry-After (seconds or HTTP date), with a one-minute floor."""
    delay = 60 * (2 ** attempt)
    value = (headers or {}).get("Retry-After", "")
    try:
        seconds = int(value)
    except (ValueError, TypeError):
        try:
            deadline = parsedate_to_datetime(value)
            seconds = (deadline - (now or datetime.now(timezone.utc))).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return delay
    return max(delay, seconds)


def fetch_url(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": f"llm-benchmark-inventory/1.0 (https://github.com/{REPOSITORY})"})
    for attempt in range(4):
        delay = 10 * (2 ** attempt)
        try:
            with urlopen(request, timeout=45) as response:
                payload = response.read(20_000_001)
                if len(payload) > 20_000_000:
                    raise ValueError("arXiv metadata response exceeds 20 MB")
                return payload
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504}:
                raise
            if error.code == 429 or (error.headers or {}).get("Retry-After"):
                delay = retry_delay(error.headers, attempt)
                error.retry_at = iso(datetime.now(timezone.utc) + timedelta(seconds=delay))
            # A long server cooldown is deferred, never shortened to fit this run.
            if attempt == 3 or delay > 240:
                raise
        except (URLError, TimeoutError):
            if attempt == 3:
                raise
        print(f"arXiv request delayed; retrying in {delay:.0f} seconds", flush=True)
        time.sleep(delay)
    raise RuntimeError("arXiv request failed")


def rss_date(value: str) -> str:
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        raise ValueError("RSS date must include a timezone")
    return iso(parsed)


def parse_rss(payload: bytes) -> tuple[str, list[dict], int]:
    root = ET.fromstring(payload)
    channel = root.find("channel")
    if root.tag != "rss" or channel is None:
        raise ValueError("arXiv did not return RSS")
    published = rss_date(channel.findtext("pubDate", ""))
    items = channel.findall("item")
    papers = []
    for item in items:
        kind = item.findtext(RSS_ARXIV + "announce_type", "")
        if kind not in {"new", "cross", "replace", "replace-cross"}:
            raise ValueError("Unknown RSS announcement type")
        if kind != "new":
            continue
        link = item.findtext("link", "")
        match = re.fullmatch(r"https?://arxiv\.org/abs/(" + ARXIV_ID + r")(?:v\d+)?", link)
        if not match:
            raise ValueError("Invalid new-paper RSS link")
        key = match[1]
        description = item.findtext("description", "")
        header, separator, summary = description.partition("Abstract:")
        if not separator or not summary.strip() or not re.search(r"arXiv:" + re.escape(key) + r"(?:v\d+)?\b", header):
            raise ValueError("RSS abstract or identifier is missing")
        announced = rss_date(item.findtext("pubDate", ""))
        if announced != published:
            raise ValueError("Mixed RSS announcement dates")
        papers.append({"arxiv_id": key, "url": f"https://arxiv.org/abs/{key}",
            "title": " ".join(item.findtext("title", "").split()),
            "summary": " ".join(summary.split()),
            # RSS creator strings may contain commas inside affiliations.
            "authors": [item.findtext(DC + "creator", "")],
            "categories": [c.text for c in item.findall("category") if c.text],
            "published": None, "updated": None, "announced_at": announced,
            "metadata_source": "rss"})
    return published, papers, len(items)


class ExpiredResumptionToken(ValueError):
    pass


def parse_oai(payload: bytes, day: str, continuation=False) -> tuple[list[dict], str, str]:
    root = ET.fromstring(payload)
    if root.tag != OAI + "OAI-PMH":
        raise ValueError("arXiv did not return OAI-PMH")
    response_date = root.findtext(OAI + "responseDate", "")
    timestamp(response_date)
    errors = root.findall(OAI + "error")
    if errors:
        if len(errors) == 1 and errors[0].get("code") == "noRecordsMatch":
            if continuation:
                raise ValueError("OAI continuation unexpectedly lost its records")
            return [], "", response_date
        if errors[0].get("code") == "badResumptionToken":
            raise ExpiredResumptionToken("Restart the unfinished OAI day")
        raise ValueError("OAI error: " + str(errors[0].get("code")))
    listing = root.find(OAI + "ListRecords")
    if listing is None:
        raise ValueError("Missing OAI records")
    papers = []
    for record in listing.findall(OAI + "record"):
        header = record.find(OAI + "header")
        if header is None or header.findtext(OAI + "datestamp") != day:
            raise ValueError("OAI record outside the requested day")
        if header.get("status") == "deleted":
            continue
        metadata = record.find(OAI + "metadata/" + OAI_ARXIV + "arXiv")
        if metadata is None:
            raise ValueError("Missing arXiv metadata")
        key = metadata.findtext(OAI_ARXIV + "id", "")
        if not re.fullmatch(ARXIV_ID, key):
            if re.fullmatch(r"[a-z-]+(?:\.[A-Z]{2})?/\d{7}", key):
                continue  # Pre-2007 identifiers are outside this LLM inventory.
            raise ValueError("Invalid OAI arXiv ID")
        if header.findtext(OAI + "identifier") != "oai:arXiv.org:" + key:
            raise ValueError("OAI header and metadata IDs disagree")
        created = metadata.findtext(OAI_ARXIV + "created", "")
        updated = metadata.findtext(OAI_ARXIV + "updated") or created
        for value in (created, updated):
            datetime.strptime(value, "%Y-%m-%d")
        authors = []
        for author in metadata.findall(OAI_ARXIV + "authors/" + OAI_ARXIV + "author"):
            authors.append(" ".join(filter(None, (author.findtext(OAI_ARXIV + "forenames"), author.findtext(OAI_ARXIV + "keyname")))))
        papers.append({"arxiv_id": key, "url": f"https://arxiv.org/abs/{key}",
            "title": " ".join(metadata.findtext(OAI_ARXIV + "title", "").split()),
            "summary": " ".join(metadata.findtext(OAI_ARXIV + "abstract", "").split()),
            "authors": authors, "categories": metadata.findtext(OAI_ARXIV + "categories", "").split(),
            "published": created + "T00:00:00Z", "updated": updated + "T00:00:00Z",
            "submission_date_precision": "day", "metadata_changed_at": day + "T00:00:00Z",
            "metadata_source": "oai"})
    token = listing.findtext(OAI + "resumptionToken", "").strip()
    if token and not listing.findall(OAI + "record"):
        raise ValueError("Empty OAI continuation page")
    return papers, token, response_date


def merge_papers(state, papers, now):
    by_id = {p["arxiv_id"]: p for p in state["papers"]}
    for paper in papers:
        key = paper["arxiv_id"]
        old = by_id.get(key)
        if old:
            # An RSS replay of v1 must never overwrite newer metadata. Discovery
            # must also preserve review status and completed investigation records.
            if paper.get("announced_at"):
                old.setdefault("announced_at", paper["announced_at"])
            if paper["metadata_source"] == "oai":
                incoming = timestamp(paper["updated"]).date()
                existing = timestamp(old["updated"]).date() if old.get("updated") else None
                if existing is None or incoming >= existing:
                    values = dict(paper)
                    # Preserve precise API timestamps when OAI only repeats a date.
                    for field in ("published", "updated"):
                        if old.get(field) and timestamp(old[field]).date() == timestamp(values[field]).date():
                            values[field] = old[field]
                    old.update(values)
        elif candidate(paper):
            by_id[key] = {**paper, "first_seen_at": iso(now), "review_status": "pending", "review_issue_url": None}
    state["papers"] = sorted(by_id.values(), key=lambda p: (p.get("announced_at") or p.get("published") or p["first_seen_at"], p["arxiv_id"]), reverse=True)


def collect(state: dict, now: datetime, fetch=None, sleep=time.sleep, *,
            checkpoint=None, allow_cached=False, feeds=RSS_FEEDS, backfill_page_limit=30) -> dict:
    """Consume new announcements and incrementally recover metadata by change date.

    RSS checkpoints describe observed feed editions, never today's wall clock.
    OAI advances only after all pages of a UTC day complete. Each page is saved,
    including its continuation token, so an interrupted run can resume.
    """
    fetch = fetch or fetch_url
    result = copy.deepcopy(state)
    discovery = result.setdefault("discovery", {})
    rss = discovery.setdefault("rss", {})
    recovery = discovery.setdefault("oai", {"next_day": (now - timedelta(days=30)).date().isoformat()})
    errors = discovery.setdefault("errors", {})
    calls = 0

    def persist():
        validate_state(result)
        if checkpoint:
            checkpoint(copy.deepcopy(result))

    def request(url):
        nonlocal calls
        if calls:
            sleep(10)
        calls += 1
        return fetch(url)

    def cooling(source):
        retry = errors.get(source, {}).get("retry_at")
        return retry and timestamp(retry) > now

    def failed(source, error):
        if not allow_cached or (isinstance(error, HTTPError) and error.code not in {429, 500, 502, 503, 504}):
            raise error
        errors[source] = {"at": iso(now), "code": f"HTTP {error.code}" if isinstance(error, HTTPError) else type(error).__name__}
        if getattr(error, "retry_at", None):
            errors[source]["retry_at"] = error.retry_at
        print(f"::warning::{source} unavailable; keeping its checkpoint and cached candidates", flush=True)
        persist()

    for name in feeds:
        source = "rss:" + name
        if cooling(source):
            continue
        try:
            published, papers, count = parse_rss(request(f"https://rss.arxiv.org/rss/{name}"))
            if timestamp(published) > now:
                raise ValueError("RSS announcement date is in the future")
            previous = rss.get(name, {}).get("pub_date")
            if not previous or timestamp(published) > timestamp(previous):
                merge_papers(result, papers, now)
                rss[name] = {"pub_date": published, "checked_at": iso(now), "items": count,
                             "possibly_truncated": count >= 2000}
            # A capped feed is still useful; OAI independently recovers missing rows.
            errors.pop(source, None)
            persist()
            print(f"RSS {name}: {published}, {count} items", flush=True)
        except (HTTPError, URLError, TimeoutError) as error:
            failed(source, error)

    # Finish closed UTC days only. Reconcile every day so capped/stale RSS feeds
    # and cross-listings are covered too. First migration recovers the last month.
    today = now.astimezone(timezone.utc).date()
    pages = 0
    restarted = False
    while datetime.strptime(recovery["next_day"], "%Y-%m-%d").date() < today and pages < backfill_page_limit:
        if cooling("oai"):
            break
        day = recovery["next_day"]
        token = recovery.get("resumption_token")
        params = {"verb": "ListRecords", "resumptionToken": token} if token else {
            "verb": "ListRecords", "metadataPrefix": "arXiv", "from": day, "until": day}
        try:
            pages += 1
            papers, following, response_date = parse_oai(request(OAI_URL + "?" + urlencode(params)), day, bool(token))
            # Cached OAI responses from before the end of this day cannot close it.
            if timestamp(response_date).date() <= datetime.strptime(day, "%Y-%m-%d").date():
                raise ValueError("OAI response predates the end of the requested day")
            if following and following == token:
                raise ValueError("OAI continuation did not advance")
            merge_papers(result, papers, now)
            if following:
                recovery["resumption_token"] = following
            else:
                recovery.pop("resumption_token", None)
                recovery["completed_through"] = day
                recovery["next_day"] = (datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)).date().isoformat()
            recovery["last_response_at"] = response_date
            errors.pop("oai", None)
            persist()
            print(f"OAI {day}: {len(papers)} records, {'more pages' if following else 'complete'}", flush=True)
        except ExpiredResumptionToken:
            if not token or restarted:
                raise
            recovery.pop("resumption_token", None)
            restarted = True
            persist()
        except (HTTPError, URLError, TimeoutError) as error:
            failed("oai", error)
            break
    discovery["recovery_pending"] = datetime.strptime(recovery["next_day"], "%Y-%m-%d").date() < today
    discovery["last_attempt_at"] = iso(now)
    if not errors:
        result["last_checked_at"] = iso(now)
    result.pop("discovery_error", None)  # Legacy search-API cooldown is source-specific.
    persist()
    return result

class GitHub:
    def __init__(self, token: str):
        if not token:
            raise ValueError("GH_TOKEN is required for issue synchronization")
        self.token = token

    def request(self, path: str, data=None, method=None):
        request = Request("https://api.github.com/repos/" + REPOSITORY + path,
                          data=json.dumps(data).encode() if data is not None else None, method=method,
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


def collect_with_cached_fallback(state, now, **kwargs):
    """Persist available sources while failed sources retain their own cursor."""
    return collect(state, now, allow_cached=True, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    parser.add_argument("--allow-cached", action="store_true", help="Investigate cached candidates if arXiv is temporarily unavailable")
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
        state = collect(state, now, allow_cached=args.allow_cached,
                        checkpoint=lambda current: save_state(args.state, current))
        # Preserve discovery even if GitHub is temporarily unavailable.
        save_state(args.state, state)
    if args.github:
        state = sync_issues(state, GitHub(os.environ.get("GH_TOKEN", "")), now, args.reviewer)
        save_state(args.state, state)
    print(f"Papers: {len(state['papers'])}; new: {len(state['papers']) - before}; proposals: {sum(p.get('analysis_status') == 'proposed' for p in state['papers'])}")


if __name__ == "__main__":
    main()

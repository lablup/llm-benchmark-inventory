#!/usr/bin/env python3
"""Publish the research funnel: what was attempted, where each paper stopped and
what reached the page (decision 22, item 4).

Reads new-papers.json, research/proposals.json and updates.json; writes
research-status.json for the site and, with --notify, appends (or, later the same day, rewrites) a one-line daily
summary in the "조사 일지" issue and the workflow step summary.
"""
import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from research_pipeline import KST, read_json, write_json

ROOT = Path(__file__).resolve().parent
OUTPUT = "research-status.json"
REPOSITORY = "lablup/llm-benchmark-inventory"
LABEL = "research-log"
STATUS_URL = "https://lablup.github.io/llm-benchmark-inventory/papers.html#research"
# Stage ids and their Korean labels, in the order the page shows them.
STAGES = {
    "published": "표에 반영",
    "awaiting": "Claude 검증 대기",
    "held": "근거 부족 보류",
    "excluded": "본문 조사 후 제외",
    "draft_rejected": "초안 형식 검사 거부",
    "card_failed": "공식 자료 확인 실패",
    "link_missing": "공식 링크 없음",
    "pdf_failed": "PDF 추출 실패",
    "screened_out": "초록 선별에서 제외",
    "queued": "본문 조사 대기",
    "unscreened": "초록 선별 대기",
}
LEDGER_STAGES = {"accepted": "published", "awaiting_claude": "awaiting", "proposed": "awaiting",
                 "needs_evidence": "held", "held": "held", "exclude": "excluded", "rejected": "excluded"}
SUMMARY_FIELDS = (("pdf_failed", "PDF 실패"), ("link_missing", "링크 없음"), ("draft_rejected", "초안 거부"), ("excluded", "제외"),
                  ("held", "보류"), ("awaiting", "검증 대기"), ("published", "표 반영"))


def kst_day(value) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(KST).date().isoformat()


def stage(paper: dict, item: dict | None) -> str:
    if item:
        return LEDGER_STAGES.get(item.get("status"), "held")
    reason = paper.get("analysis_reason") or ""
    status = paper.get("analysis_status")
    if reason.startswith("PDF 추출 실패"):
        return "pdf_failed"
    if reason.startswith("Claude 응답 처리 실패"):
        return "draft_rejected"
    if reason.startswith("공식 자료 확인 실패"):
        return "card_failed"
    if reason.startswith("공식 저장소 링크 없음"):
        return "link_missing"
    if status == "exclude":
        return "screened_out"
    if status in {"queued", "needs_evidence", "awaiting_claude"}:
        return "queued"
    return "unscreened"


def paper_record(paper: dict, item: dict | None, applied: dict) -> dict:
    key = paper["arxiv_id"]
    current = stage(paper, item)
    record = {"arxiv_id": key, "title": paper.get("title", ""), "first_seen": (paper.get("first_seen_at") or "")[:10],
              "stage": current, "stage_label": STAGES[current],
              "reason": ((item or {}).get("reason") or paper.get("analysis_reason") or "")[:600],
              "updated_at": (item or {}).get("applied_at") or (item or {}).get("created_at") or paper.get("analysis_at")}
    if paper.get("analysis_retry_after"):
        record["retry_after"] = paper["analysis_retry_after"]
    if current == "published" and key in applied:
        update = applied[key]
        record["changes"] = [c["name"] for c in update["changes"]]
        record["inventory_url"] = next((c["inventory_url"] for c in update["changes"]), None)
    return record


def day_records(ledger: dict, papers: dict, items: dict, applied: dict) -> list[dict]:
    runs = {}
    for source in ("claude_daily_runs", "daily_runs"):
        for day, run in (ledger.get(source) or {}).items():
            merged = runs.setdefault(day, {"attempted": [], "abstracts": 0, "calls": 0, "cost_usd": 0.0})
            merged["attempted"].extend(k for k in run.get("attempted", []) if k not in merged["attempted"])
            merged["abstracts"] += len(run.get("abstract_attempted", []))
            merged["calls"] += int(run.get("calls") or 0)
            merged["cost_usd"] = round(merged["cost_usd"] + float(run.get("cost_usd") or 0), 2)
    published_by_day = {}
    for key, update in applied.items():
        published_by_day.setdefault(kst_day(update.get("applied_at")), []).append(key)
    days = []
    for day in sorted(set(runs) | set(k for k in published_by_day if k)):
        run = runs.get(day, {"attempted": [], "abstracts": 0, "calls": 0, "cost_usd": 0.0})
        counts = dict.fromkeys(STAGES, 0)
        counts["carried"] = 0
        for key in run["attempted"]:
            paper, item = papers.get(key, {"arxiv_id": key}), items.get(key)
            if item and kst_day(item.get("created_at")) != day:
                counts["carried"] += 1  # attempted this day, concluded on another
            else:
                counts[stage(paper, item)] += 1
        counts["published"] = len(published_by_day.get(day, []))
        days.append({"day": day, "abstracts": run["abstracts"], "attempted": len(run["attempted"]),
                     "calls": run["calls"], "cost_usd": run["cost_usd"], "counts": counts})
    return days


def build(root: Path = ROOT) -> dict:
    state = read_json(root / "new-papers.json")
    ledger = read_json(root / "research/proposals.json")
    updates_path = root / "updates.json"
    updates = read_json(updates_path)["updates"] if updates_path.exists() else []
    applied = {u["arxiv_id"]: u for u in updates}
    papers = {p["arxiv_id"]: p for p in state.get("papers", [])}
    items = ledger.get("proposals", {})
    records = [paper_record(p, items.get(k), applied) for k, p in papers.items()]
    records.sort(key=lambda r: (r["updated_at"] or "", r["first_seen"], r["arxiv_id"]), reverse=True)
    totals = dict.fromkeys(STAGES, 0)
    for record in records:
        totals[record["stage"]] += 1
    result = {"schema_version": 1, "last_checked_at": state.get("last_checked_at"),
              "last_run_at": (state.get("research") or {}).get("last_run_at"),
              "run_status": (state.get("research") or {}).get("status"),
              "stages": STAGES, "totals": {"papers": len(records), **totals},
              "days": day_records(ledger, papers, items, applied), "papers": records}
    write_json(root / OUTPUT, result)
    return result


def summary_line(status: dict, day: str | None = None) -> str:
    days = status["days"]
    record = next((d for d in days if d["day"] == day), None) if day else (days[-1] if days else None)
    if record is None:
        return f"{day or '오늘'}: 자동 조사 실행 기록이 없습니다."
    parts = [f"초록 선별 {record['abstracts']}건", f"본문 시도 {record['attempted']}건"]
    parts += [f"{label} {record['counts'][key]}건" for key, label in SUMMARY_FIELDS]
    parts.append(f"대기열 {status['totals']['queued']}건")
    if record.get("calls"):
        # What the API would have charged for the subscription calls (decision 23).
        parts.append(f"API 환산 비용 ${record['cost_usd']:.2f}(Claude 호출 {record['calls']}회)")
    return f"{record['day']}: " + " · ".join(parts)


def markdown_title(title: str, limit: int = 120) -> str:
    title = " ".join(title.split()).replace("@", "＠").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", title[:limit])


def comment_body(status: dict, day: str) -> str:
    lines = [f"<!-- research-log:{day} -->", summary_line(status, day), ""]
    concluded = [p for p in status["papers"] if kst_day(p.get("updated_at")) == day
                 and p["stage"] in {"published", "awaiting", "held", "excluded"}]
    for record in concluded[:40]:
        lines.append(f"- {record['stage_label']} · [{markdown_title(record['title'])}](https://arxiv.org/abs/{record['arxiv_id']})"
                     + (f" → [표의 행](https://lablup.github.io/llm-benchmark-inventory/{record['inventory_url'].removeprefix('./')})"
                        if record.get("inventory_url") else ""))
    lines += ["", f"[조사 현황 페이지]({STATUS_URL}) · 보류 사유와 재시도 예정일은 페이지에서 논문별로 볼 수 있습니다."]
    return "\n".join(lines)


class GitHub:
    def __init__(self, token: str):
        if not token:
            raise ValueError("GH_TOKEN is required to post the research summary")
        self.token = token

    def request(self, path: str, data=None, method=None):
        import json
        request = Request("https://api.github.com/repos/" + REPOSITORY + path,
                          data=json.dumps(data).encode() if data is not None else None, method=method,
                          headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "llm-benchmark-inventory"})
        with urlopen(request, timeout=45) as response:
            return json.load(response)


def notify(github, status: dict, day: str, reviewer: str) -> str | None:
    """Append the day's line to the open 조사 일지 issue, creating it once; idempotent per day."""
    try:
        github.request(f"/labels/{LABEL}")
    except HTTPError as error:
        if error.code != 404:
            raise
        github.request("/labels", {"name": LABEL, "color": "5319e7", "description": "Daily automated research summary"})
    issues = [i for i in github.request(f"/issues?state=open&labels={LABEL}&per_page=100") if "pull_request" not in i]
    if issues:
        issue = sorted(issues, key=lambda i: i["number"])[0]
    else:
        issue = github.request("/issues", {
            "title": "[조사 일지] 자동 논문 조사 하루 요약",
            "body": "\n".join([f"@{reviewer} 매일 자동 조사가 끝나면 이 이슈에 한 줄 요약을 댓글로 남깁니다.",
                               "닫지 않고 두면 알림으로 받을 수 있습니다. 논문별 단계와 사유는 "
                               f"[조사 현황 페이지]({STATUS_URL})에 있습니다."]),
            "labels": [LABEL], "assignees": [reviewer]})
    marker = f"<!-- research-log:{day} -->"
    body = comment_body(status, day)
    page = 1
    while True:
        comments = github.request(f"/issues/{issue['number']}/comments?per_page=100&page={page}")
        existing = next((c for c in comments if marker in (c.get("body") or "")), None)
        if existing:
            if (existing.get("body") or "") == body:
                return None
            # A later run on the same day (a re-audit, a retry) rewrites the day's line
            # rather than adding a second comment or leaving the first one stale.
            updated = github.request(f"/issues/comments/{existing['id']}", {"body": body}, method="PATCH")
            return updated.get("html_url")
        if len(comments) < 100:
            break
        page += 1
    created = github.request(f"/issues/{issue['number']}/comments", {"body": body})
    return created.get("html_url")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notify", action="store_true", help="Post today's summary to the 조사 일지 issue")
    parser.add_argument("--day", help="KST day to summarise (default: today)")
    args = parser.parse_args(argv)
    status = build()
    day = args.day or datetime.now(timezone.utc).astimezone(KST).date().isoformat()
    line = summary_line(status, day)
    print(line)
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        Path(summary_file).open("a", encoding="utf-8").write(f"\n{line}\n")
    if args.notify:
        url = notify(GitHub(os.environ.get("GH_TOKEN", "")), status, day, os.environ.get("ARXIV_REVIEWER", "songys"))
        print(f"Research summary comment: {url or 'already posted'}")


if __name__ == "__main__":
    sys.exit(main())

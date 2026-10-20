#!/usr/bin/env python3
"""Publish researched proposals and apply an authorized reviewer's exact commands."""
from __future__ import annotations

import copy
import csv
import io
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from arxiv_watch import ROOT, KST, iso, LABEL, REPOSITORY, GitHub, markdown_title, load_state, save_state
from research_pipeline import TABLES, digest, read_json, write_json, read_table, copy_block

MARKER = re.compile(r"^<!-- arxiv-proposals:v2:(\d{4}-\d{2}-\d{2}) -->", re.M)
ENTRY = re.compile(r"<!-- proposal:(\d{4}\.\d{4,5}):([a-f0-9]{64}) -->")
COMMAND = re.compile(r"(추가|보류|제외)\s+(\d{4}\.\d{4,5})")
FILES = [*TABLES.values(), "english-copy.js", "benchmark-modalities.json", "README.md",
         "inventory-data.js", "serving-data.js", "site-meta.js", "benchmark_top_models.csv"]


def proposal_hash(proposal):
    return digest({k: proposal[k] for k in ("arxiv_id", "changes", "source")})


def issue_body(proposals, day, reviewer):
    lines = [f"<!-- arxiv-proposals:v2:{day} -->", f"@{reviewer} 조사와 자동 대조를 마친 표 변경안 {len(proposals)}건입니다.", "",
             "아래 변경 내용과 남은 확인 사항을 검토해 주세요. 전체 논문을 읽는 작업은 요청하지 않습니다.",
             "각 항목은 댓글 한 줄로 처리합니다: `추가 arXiv번호`, `보류 arXiv번호`, `제외 arXiv번호`.",
             "추가는 표시된 변경안을 CSV와 페이지에 반영합니다. 보류·제외는 반복 알림을 멈춥니다.",
             "보류한 항목은 같은 이슈에 추가 또는 제외를 다시 남길 수 있습니다. 체크박스는 사용하지 않습니다.",
             "자동 대조는 같은 모델의 별도 요청이며, 사람이 사실을 검증했다는 뜻은 아닙니다.", ""]
    for item in proposals:
        lines.extend([f"## {markdown_title(item['paper_title'])}", f"<!-- proposal:{item['arxiv_id']}:{item['proposal_sha256']} -->",
                      f"arXiv `{item['arxiv_id']}` · [논문 PDF]({item['source']['url']})", "",
                      markdown_title(item["reason"]), ""])
        quotes = set()
        for change in item["changes"]:
            lines += [f"### {change['track']} · {markdown_title(change['row']['이름'])}", "", "| 항목 | 현재 | 변경 후 |", "|---|---|---|"]
            before = change["before"] or {}
            for key, value in change["row"].items():
                if before.get(key) != value:
                    # Keep the complete proposed text visible, even for long definitions.
                    safe = lambda x: markdown_title(str(x), limit=2000)
                    lines.append(f"| {safe(key)} | {safe(before.get(key, '새 항목'))} | {safe(value)} |")
            lines += ["", f"입력 유형: {change['modality']}", ""]
            if change["track"] == "en":
                lines += ["영문 화면 문구:", ""]
                for key, value in change["english_copy"].items():
                    lines.append(f"- {key}: {safe(value)}")
            lines += ["", "원문 근거:"]
            for field, ev in change["evidence"].items():
                quote = ev["quote"]
                if quote not in quotes:
                    lines.append(f"- p.{ev['page']}: {markdown_title(quote)}")
                    quotes.add(quote)
            lines.append("")
        lines += ["남은 확인: 데이터셋 라이선스와 lm-eval 지원은 확인되지 않은 상태일 수 있습니다. 표에 적힌 상태를 확인해 주세요.",
                  f"승인 댓글: `추가 {item['arxiv_id']}`", ""]
    body = "\n".join(lines)
    if len(body) > 60000:
        raise ValueError("Proposal digest is too long; reduce the daily batch")
    return body


def replace_copy(text, key, fields):
    import json
    entry = "  " + json.dumps(key) + ": " + json.dumps(fields, ensure_ascii=False, indent=2).replace("\n", "\n  ") + ","
    pattern = re.compile(r'^  (?:"' + re.escape(key) + r'"|' + re.escape(key) + r'):\s*\{.*?^  \},?', re.M | re.S)
    if pattern.search(text):
        return pattern.sub(lambda _: entry, text, count=1)
    if not text.rstrip().endswith("};"):
        raise ValueError("Unrecognized English display copy format")
    return text.rstrip()[:-2] + entry + "\n};\n"


def apply_proposal(item, root=ROOT, verify=True):
    if item["proposal_sha256"] != proposal_hash(item) or not item.get("verification", {}).get("approve"):
        raise ValueError("Proposal hash or second-pass verification is invalid")
    config = read_json(root / "research/config.json")
    if config.get("publication_policy") == "complete-evidence-v1":
        from publication_checks import complete
        complete(item["changes"])
        if item.get("verification", {}).get("publication_policy") != config["publication_policy"]:
            raise ValueError("Proposal lacks approval under the complete publication policy")
        if not agreed(item, config):
            raise ValueError("Complete proposal is not bound to the current Claude approval")
    originals = {name: (root / name).read_bytes() for name in FILES}
    tables = {track: read_table(root, track) for track in TABLES}
    # Check every row before writing anything, so an unrelated update is retained.
    for change in item["changes"]:
        current = next((row for row in tables[change["track"]][1] if row["id"] == change["row"]["id"]), None)
        if change["track"] == "en" and digest(copy_block((root / "english-copy.js").read_text(), change["row"]["id"])) != change["english_before_sha256"]:
            raise ValueError("English display copy changed after this proposal")
        if digest(current) != change["before_sha256"]:
            raise ValueError("The inventory row changed after this proposal; investigate again before approval")
    try:
        modalities = read_json(root / "benchmark-modalities.json")
        for change in item["changes"]:
            track, row = change["track"], change["row"]
            headers, rows = tables[track]
            index = next((i for i, old in enumerate(rows) if old["id"] == row["id"]), None)
            if index is None:
                rows.append(row)
            else:
                rows[index] = row
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            (root / TABLES[track]).write_text(stream.getvalue(), encoding="utf-8-sig")
            if track == "en":
                path = root / "english-copy.js"
                path.write_text(replace_copy(path.read_text(), row["id"], change["english_copy"]), encoding="utf-8")
            modalities[row["id"]] = change["modality"]
        if config.get("publication_policy") == "complete-evidence-v1":
            from publication_checks import apply_rankings
            apply_rankings(item, root)
        write_json(root / "benchmark-modalities.json", modalities)
        if verify:
            # Reuse the existing renderer without re-normalizing license fields.
            subprocess.run([sys.executable, "-c", "import build_benchmark_inventory as b; import research_pipeline as r; b.ROOT.joinpath('README.md').write_text(b.render_readme({name:r.read_table(b.ROOT,track)[1] for track,name in r.TABLES.items()}),encoding='utf-8')"], cwd=root, check=True)
            subprocess.run([sys.executable, "build_site_data.py"], cwd=root, check=True)
            subprocess.run([sys.executable, "validate_inventory.py"], cwd=root, check=True)
            subprocess.run(["node", "--check", "english-copy.js"], cwd=root, check=True)
    except BaseException:
        for name, content in originals.items():
            (root / name).write_bytes(content)
        raise


def comments(github, number):
    page = 1
    while True:
        batch = github.request(f"/issues/{number}/comments?per_page=100&page={page}")
        yield from batch
        if len(batch) < 100:
            break
        page += 1


def process_comment(comment, issue, ledger, reviewer, root=ROOT, apply=apply_proposal):
    if comment["id"] in ledger["processed_comments"] or comment.get("user", {}).get("login") != reviewer:
        return False
    # Exact whole-comment commands only; prose/quotes/code fences have no effect.
    match = COMMAND.fullmatch((comment.get("body") or "").strip())
    if not match:
        return False
    action, key = match.groups()
    item = ledger["proposals"].get(key)
    entries = dict(ENTRY.findall(issue.get("body") or ""))
    if (not item or entries.get(key) != item["proposal_sha256"] or
        item["proposal_sha256"] != proposal_hash(item) or item.get("issue_url") != issue["html_url"] or
        issue.get("user", {}).get("login") != "github-actions[bot]" or not MARKER.search(issue.get("body") or "")):
        return False
    if item["status"] in {"accepted", "rejected"}:
        ledger["processed_comments"].append(comment["id"])
        return False
    if action == "추가":
        apply(item, root)
        item["status"] = "accepted"
    else:
        item["status"] = "held" if action == "보류" else "rejected"
    item["decision_comment_url"] = comment["html_url"]
    ledger["processed_comments"].append(comment["id"])
    return True


AUTO_MARKER = re.compile(r"^<!-- arxiv-applied:v3:(\d{4}-\d{2}-\d{2}) -->", re.M)


def agreed(item, config):
    verification = item.get("verification", {})
    votes = verification.get("votes", [])
    if config.get("publication_policy") == "complete-evidence-v1":
        from publication_checks import complete
        if verification.get("publication_policy") != config["publication_policy"]:
            return False
        try:
            complete(item["changes"])
        except (ValueError, KeyError, TypeError):
            return False
    if config.get("approval_policy") == "claude_only":
        return (verification.get("policy") == "claude_only"
                and len(votes) == 1 and votes[0].get("model") == config.get("claude_model")
                and votes[0].get("approve") is True
                and votes[0].get("auth_method") == "oauth_token"
                and verification.get("approve") is True
                and verification.get("reviewed_sha256") == item["proposal_sha256"] == proposal_hash(item))
    expected = {config.get("model"), config.get("verifier_model")}
    return (len(expected) == 2 and None not in expected and len(votes) == 2
            and {vote.get("model") for vote in votes} == expected
            and all(vote.get("approve") is True for vote in votes)
            and verification.get("approve") is True
            and verification.get("reviewed_sha256") == item["proposal_sha256"] == proposal_hash(item))


def sync_automatic(state, ledger, github, config, root, now):
    for item in ledger["proposals"].values():
        if item["status"] != "proposed":
            continue
        if not agreed(item, config):
            item["status"] = "needs_evidence"
            item["reason"] = "현재 승인 정책에 맞는 검증 기록이 없어 반영하지 않았습니다."
            continue
        try:
            apply_proposal(item, root)
        except ValueError as error:
            item["status"] = "needs_evidence"
            item["reason"] = "조사 이후 기존 자료가 변경되어 반영하지 않았습니다."
            print(f"Skipped {item['arxiv_id']}: {type(error).__name__}")
            continue
        item["status"] = "accepted"
        item["applied_by"] = "claude_approval" if config.get("approval_policy") == "claude_only" else "dual_model_agreement"
        item["applied_at"] = iso(now)
    # Notification runs after deployment. Recover its links on the next sync.
    for issue in github.issues():
        body = issue.get("body") or ""
        if issue.get("user", {}).get("login") != "github-actions[bot]" or not AUTO_MARKER.search(body):
            continue
        for key, sha in ENTRY.findall(body):
            item = ledger["proposals"].get(key)
            if item and item["status"] == "accepted" and item["proposal_sha256"] == sha:
                item["issue_url"] = issue["html_url"]
    for paper in state["papers"]:
        item = ledger["proposals"].get(paper["arxiv_id"])
        if item:
            paper.update(analysis_status=item["status"], analysis_reason=item["reason"],
                         review_issue_url=item.get("issue_url"),
                         review_status="reviewed" if item["status"] == "accepted" else "pending")
    write_json(root / "research/proposals.json", ledger)
    return state


def notify_applied(github, root, now):
    ledger = read_json(root / "research/proposals.json")
    day = now.astimezone(KST).date().isoformat()
    seen = set()
    today = False
    for issue in github.issues():
        body = issue.get("body") or ""
        marker = AUTO_MARKER.search(body)
        if not marker or issue.get("user", {}).get("login") != "github-actions[bot]":
            continue
        seen.update(ENTRY.findall(body))
        today |= marker[1] == day
        if issue.get("state") == "open":
            github.request(f"/issues/{issue['number']}", {"state": "closed", "state_reason": "completed"}, method="PATCH")
    pending = [item for item in ledger["proposals"].values() if item["status"] == "accepted"
               and item.get("applied_by") in {"dual_model_agreement", "claude_approval"}
               and (item["arxiv_id"], item["proposal_sha256"]) not in seen]
    if not pending or today:
        return
    batch = pending[:100]
    reviewer = os.environ.get("ARXIV_REVIEWER", "songys")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    lines = [f"<!-- arxiv-applied:v3:{day} -->", f"@{reviewer} 승인과 근거 확인을 통과한 {len(batch)}건을 표와 페이지에 반영했습니다.", "",
             "검토나 승인 댓글은 필요하지 않습니다. 승인되지 않았거나 근거가 부족한 항목은 반영하지 않았습니다.",
             f"[페이지](https://lablup.github.io/llm-benchmark-inventory/) · [변경 기록](https://github.com/{REPOSITORY}/commit/{commit})", ""]
    for item in batch:
        lines += [f"## {markdown_title(item['paper_title'], limit=120)}", f"<!-- proposal:{item['arxiv_id']}:{item['proposal_sha256']} -->",
                  f"[논문]({item['source']['url']})", ""]
        for change in item["changes"]:
            lines.append(f"- {change['track']} / {markdown_title(change['row']['이름'], limit=100)}: " + ("새 항목 추가" if change["before"] is None else "기존 항목 수정"))
        lines.append("")
    github.ensure_label()
    issue = github.request("/issues", {"title": f"[자동 반영] {day} · 벤치마크 {len(batch)}건",
        "body": "\n".join(lines), "labels": [LABEL], "assignees": [reviewer]})
    github.request(f"/issues/{issue['number']}", {"state": "closed", "state_reason": "completed"}, method="PATCH")


def _sync(state, github, now, reviewer, root=ROOT):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", reviewer):
        raise ValueError("Invalid reviewer")
    result = copy.deepcopy(state)
    ledger = read_json(root / "research/proposals.json")
    config = read_json(root / "research/config.json")
    if config.get("auto_apply_agreed"):
        return sync_automatic(result, ledger, github, config, root, now)
    day = now.astimezone(KST).date().isoformat()
    daily_exists = False
    for issue in sorted(github.issues(), key=lambda x: x["number"]):
        body = issue.get("body") or ""
        marker = MARKER.search(body)
        if not marker or issue.get("user", {}).get("login") != "github-actions[bot]":
            continue
        daily_exists |= marker[1] == day
        for key, sha in ENTRY.findall(body):
            item = ledger["proposals"].get(key)
            if item and item["proposal_sha256"] == sha:
                item["issue_url"] = issue["html_url"]
        for comment in comments(github, issue["number"]):
            process_comment(comment, issue, ledger, reviewer, root)
    pending = [p for p in ledger["proposals"].values() if p["status"] == "proposed" and not p.get("issue_url")]
    if pending and not daily_exists:
        github.ensure_label()
        batch = pending[:100]
        issue = github.request("/issues", {"title": f"[표 변경안] {day} · 조사 완료 {len(batch)}건",
            "body": issue_body(batch, day, reviewer), "labels": [LABEL], "assignees": [reviewer]})
        for item in batch:
            item["issue_url"] = issue["html_url"]
    for paper in result["papers"]:
        item = ledger["proposals"].get(paper["arxiv_id"])
        paper["review_issue_url"] = item.get("issue_url") if item else None
        paper["analysis_status"] = item["status"] if item else paper.get("analysis_status", "queued")
        if item:
            paper["analysis_reason"] = item["reason"]
        paper["review_status"] = "reviewed" if item and item["status"] in {"accepted", "held", "rejected"} else "pending"
    write_json(root / "research/proposals.json", ledger)
    return result


def sync(state, github, now, reviewer, root=ROOT):
    names = FILES + ["research/proposals.json"]
    originals = {name: (root / name).read_bytes() for name in names if (root / name).exists()}
    try:
        return _sync(state, github, now, reviewer, root)
    except BaseException:
        for name, content in originals.items():
            (root / name).write_bytes(content)
        raise


def acknowledge(github, root=ROOT):
    if read_json(root / "research/config.json").get("auto_apply_agreed"):
        return notify_applied(github, root, datetime.now(timezone.utc))
    ledger = read_json(root / "research/proposals.json")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    for item in ledger["proposals"].values():
        if not item.get("decision_comment_url"):
            continue
        number = int(item["issue_url"].rsplit("/", 1)[1])
        comment_id = item["decision_comment_url"].rsplit("-", 1)[1]
        marker = f"<!-- proposal-decision:{comment_id} -->"
        if any(marker in (c.get("body") or "") and c.get("user", {}).get("login") == "github-actions[bot]" for c in comments(github, number)):
            continue
        status = {"accepted": "표에 반영했습니다", "held": "보류했습니다", "rejected": "제외했습니다"}[item["status"]]
        github.request(f"/issues/{number}/comments", {"body": f"{marker}\n{item['arxiv_id']}: {status}. [반영 기록](https://github.com/{REPOSITORY}/commit/{commit})"})


if __name__ == "__main__":
    github = GitHub(os.environ.get("GH_TOKEN", ""))
    if "--acknowledge" in sys.argv:
        acknowledge(github)
    else:
        state = load_state(ROOT / "new-papers.json")
        state = sync(state, github, datetime.now(timezone.utc), os.environ.get("ARXIV_REVIEWER", "songys"))
        save_state(ROOT / "new-papers.json", state)

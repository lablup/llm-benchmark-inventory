"""Subscription-only Claude Code audits, with durable pending proposals.

The official CLI owns authentication and transport. This module only supplies
evidence and validates its output; it never calls an Anthropic API itself.
"""
import argparse
import copy
import hashlib
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import research_pipeline as r
from claude_subscription_trial import MODEL, parse_execution
from replay_citations import correct_pages, load_evidence, verify_baseline


def call(prompt, folder, parse=r.parse_check):
    """Reuse only complete results bound to the exact input; never paid fallback."""
    folder.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(prompt.encode()).hexdigest()
    output = folder / f"{key}.claude.json"
    if output.exists():
        saved = r.read_json(output)
        if saved.get("prompt_sha256") != key or saved.get("auth_method") != "oauth_token":
            raise ValueError("Claude response provenance mismatch")
        return {**parse_execution(saved["messages"], parse), "auth_method": "oauth_token"}
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not token:
        raise RuntimeError("Claude subscription token is missing; candidate remains pending")
    # Isolated HOME/settings and an environment allowlist prevent API keys,
    # cloud configuration, local helpers, hooks and MCP servers from taking over.
    with tempfile.TemporaryDirectory(prefix="inventory-claude-") as directory:
        env = {k: os.environ[k] for k in ("PATH", "TMPDIR", "LANG", "SYSTEMROOT") if k in os.environ}
        env.update(HOME=directory, CLAUDE_CONFIG_DIR=directory,
                   CLAUDE_CODE_OAUTH_TOKEN=token, DISABLE_AUTOUPDATER="1")
        status = subprocess.run(["claude", "auth", "status"], env=env, cwd=directory,
                                capture_output=True, text=True, timeout=30)
        if status.returncode or json.loads(status.stdout).get("authMethod") != "oauth_token":
            raise RuntimeError("Claude subscription authentication could not be confirmed")
        command = ["claude", "-p", "--model", MODEL, "--max-turns", "2",
                   "--output-format", "stream-json", "--verbose",
                   "--tools", "", "--disallowedTools", "*",
                   "--setting-sources", "", "--settings", '{"disableAllHooks":true}',
                   "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                   "--no-session-persistence"]
        # Direct argv preserves empty values, unlike the action's argument parser.
        process = subprocess.run(command, input=prompt, env=env, cwd=directory,
                                 capture_output=True, text=True, timeout=600)
    try:
        messages = [json.loads(line) for line in process.stdout.splitlines() if line.strip()]
    except ValueError:
        raise RuntimeError("Claude returned an invalid execution stream; candidate remains pending") from None
    # Logs contain evidence/results only, never stderr or authentication output.
    r.write_json(folder / f"{key}.attempt.json", {
        "prompt_sha256": key, "returncode": process.returncode, "messages": messages})
    if process.returncode:
        raise RuntimeError("Claude stopped (quota/authentication/runtime); inspect the saved execution result")
    result = parse_execution(messages, parse)
    r.write_json(output, {"prompt_sha256": key, "auth_method": "oauth_token", "messages": messages})
    return {**result, "auth_method": "oauth_token"}


def audit_and_save(root, ledger, state, paper, proposal, context, config, author):
    """Checkpoint before Claude; missing/invalid responses stay pending, not rejected."""
    if config.get("approval_policy") != "claude_only":
        raise ValueError("Claude approval policy is required")
    key = paper["arxiv_id"]
    source = {k: v for k, v in context["source"].items() if k != "pages"}
    proposal = copy.deepcopy(proposal)
    proposal.pop("verification", None)
    item = {**proposal, "arxiv_id": key, "paper_title": paper["title"],
            "paper_updated": paper["updated"], "source": source,
            "status": "awaiting_claude", "created_at": r.iso(datetime.now(timezone.utc)),
            "extraction_model": author, "issue_url": None,
            "screening": ledger.get("screenings", {}).get(key),
            "claude_pending": {"source_run": os.environ.get("GITHUB_RUN_ID"),
                               "context_sha256": r.digest(context)}}
    item["proposal_sha256"] = r.digest({k: item[k] for k in ("arxiv_id", "changes", "source")})
    ledger["proposals"][key] = item
    # The API draft call has completed. Claude resumption has its own checkpoint.
    day = datetime.now(timezone.utc).astimezone(r.KST).date().isoformat()
    if day in ledger.get("daily_runs", {}):
        ledger["daily_runs"][day]["blocked"] = False
    paper.update(analysis_status="awaiting_claude", analysis_reason="Claude 근거 검증 대기")
    r.save_state(root / "new-papers.json", state)
    r.paid_call_checkpoint(root, ledger)
    # Persist the complete input as a diagnostic artifact for resumption.
    folder = root / ".research-cache" / "claude" / key
    r.write_json(folder / "context.json", context)
    audit_prompt = r.VERIFY_PROMPT
    if config.get("publication_policy") == "complete-evidence-v1":
        import publication_checks as publication
        if not item.get("changes") or not all(c.get("recommendations") and c.get("rights_evidence") for c in item["changes"]):
            completion_prompt = (publication.PROMPT + "\n" + r.evidence_payload(context)
                                 + "\nUNPUBLISHED DRAFT:\n" + json.dumps(proposal, ensure_ascii=False))
            completed = call(completion_prompt, folder / "completion",
                             lambda text: publication.validate(r.load_json_answer(text), context, root))
            proposal = {k: completed[k] for k in ("decision", "reason", "changes")}
        else:
            proposal = publication.validate(proposal, context, root)
        item.update(proposal)
        item["publication_policy"] = publication.POLICY
        item["proposal_sha256"] = r.digest({k: item[k] for k in ("arxiv_id", "changes", "source")})
        if proposal["decision"] != "propose":
            item.update(status="needs_evidence", approval_policy="claude_only")
            item.pop("claude_pending", None)
            paper.update(analysis_status=item["status"], analysis_reason=item["reason"])
            r.save_state(root / "new-papers.json", state)
            r.paid_call_checkpoint(root, ledger)
            print(f"{key}: incomplete publication evidence, held", flush=True)
            return item
        # Persist the completed draft before its separate, content-bound audit.
        r.paid_call_checkpoint(root, ledger)
        audit_prompt = publication.AUDIT_PROMPT
    prompt = audit_prompt + "\n" + r.evidence_payload(context) + "\nPROPOSAL:\n" + json.dumps(
        {k: proposal[k] for k in ("decision", "reason", "changes")}, ensure_ascii=False)
    vote = call(prompt, folder)
    item["verification"] = {"policy": "claude_only", "approve": vote["approve"],
                            "votes": [vote], "reviewed_sha256": item["proposal_sha256"]}
    if config.get("publication_policy"):
        item["verification"]["publication_policy"] = config["publication_policy"]
    item.pop("claude_pending")
    if vote["approve"]:
        item["status"] = "proposed"
    else:
        item.update(status="needs_evidence", decision="needs_evidence",
                    reason="Claude가 근거 부족으로 반영을 승인하지 않았습니다: " + vote["reason"])
        # Retain the rejected draft for a future evidence-based correction.
    paper.update(analysis_status=item["status"], analysis_reason=item["reason"])
    r.write_json(root / "research/proposals.json", ledger)
    r.save_state(root / "new-papers.json", state)
    print(f"{key}: Claude {item['status']}", flush=True)
    return item


def hold_pending(root, ledger, state, key, item, error):
    """Hold one candidate whose saved draft can no longer be resumed; nothing is applied."""
    message = str(error)[:300]
    # audit_and_save may already have replaced the ledger entry with a fresh
    # awaiting_claude record (new created_at, new claude_pending) before the
    # publication completion failed; hold the record the ledger holds now.
    item = ledger["proposals"].get(key, item)
    item.update(status="needs_evidence", decision="needs_evidence", approval_policy="claude_only",
                reason=f"저장된 초안을 재개할 수 없어 보류했습니다. 재감사(reaudit) 요청이 필요합니다: {message}",
                resume_error=message)
    item.pop("claude_pending", None)
    paper = next((p for p in state["papers"] if p["arxiv_id"] == key), None)
    if paper is not None:
        paper.update(analysis_status="needs_evidence", analysis_reason=item["reason"])
    r.write_json(root / "research/proposals.json", ledger)
    r.save_state(root / "new-papers.json", state)
    print(f"{key}: resume failed, candidate held: {message}", flush=True)


def resume_pending(root, ledger, state, config, deadline):
    for key, item in list(ledger["proposals"].items()):
        if item.get("status") != "awaiting_claude" or time.monotonic() >= deadline:
            continue
        try:
            resume_one(root, ledger, state, config, key, item)
        except (json.JSONDecodeError, subprocess.CalledProcessError) as error:
            # An empty or non-JSON Claude answer, or a failed artifact download, must
            # not end the whole run; the candidate stays pending for the next run.
            print(f"{key}: resume skipped, still pending: {str(error)[:300]}", flush=True)
        except ValueError as error:
            # A stale draft (changed vocabulary, changed inventory, hash or provenance
            # mismatch, unavailable evidence) holds only this candidate. Later
            # candidates and the day's new papers still run. Token and quota errors
            # (RuntimeError) still stop the run so no budget checkpoint is lost.
            hold_pending(root, ledger, state, key, item, error)


def resume_one(root, ledger, state, config, key, item):
    if True:
        folder = root / ".research-cache" / "claude" / key
        context_file = folder / "context.json"
        if not context_file.exists():
            run_id = item["claude_pending"].get("source_run")
            if not run_id or not str(run_id).isdigit():
                raise ValueError(f"{key}: restore the pending Claude evidence artifact before resuming")
            destination = root / ".research-cache" / "resume" / str(run_id)
            if not destination.exists():
                subprocess.run(["gh", "run", "download", str(run_id), "--repo",
                                "lablup/llm-benchmark-inventory", "--name",
                                f"research-logs-{run_id}", "--dir", str(destination)], check=True)
            matches = list(destination.rglob(f"claude/{key}/context.json"))
            if len(matches) != 1:
                raise ValueError(f"{key}: pending evidence artifact unavailable; no repeated draft call")
            context_file = matches[0]
            # Reuse any completed answer if a previous runner stopped after saving it.
            folder.mkdir(parents=True, exist_ok=True)
            for saved in context_file.parent.glob("*.claude.json"):
                (folder / saved.name).write_bytes(saved.read_bytes())
        context = r.read_json(context_file)
        if r.digest(context) != item["claude_pending"]["context_sha256"]:
            raise ValueError("Pending evidence context hash mismatch")
        if {k: v for k, v in context["source"].items() if k != "pages"} != item["source"]:
            raise ValueError("Pending source provenance changed")
        # Verify extracted pages against the saved source, and current rows again.
        context["tables"] = {track: dict(zip(("headers", "rows"), r.read_table(root, track))) for track in r.TABLES}
        context["english_copy"] = (root / "english-copy.js").read_text()
        for change in item["changes"]:
            current = next((x for x in context["tables"][change["track"]]["rows"] if x["id"] == change["row"]["id"]), None)
            if r.digest(current) != change["before_sha256"]:
                raise ValueError("Inventory changed while awaiting Claude")
            if change["track"] == "en" and r.digest(r.copy_block(context["english_copy"], change["row"]["id"])) != change["english_before_sha256"]:
                raise ValueError("English copy changed while awaiting Claude")
        paper = next(p for p in state["papers"] if p["arxiv_id"] == key)
        proposal = {k: copy.deepcopy(item[k]) for k in ("decision", "reason", "changes")}
        if config.get("publication_policy") == "complete-evidence-v1" and all(c.get("recommendations") for c in proposal["changes"]):
            import publication_checks as publication
            rankings = publication.read_rankings(root)
            for change in proposal["changes"]:
                previous = [row for row in rankings if row["benchmark_id"] == change["row"]["id"]]
                if r.digest(previous) != change.get("recommendations_before_sha256"):
                    raise ValueError("Model scores changed while awaiting Claude")
            publication.validate(proposal, context, root)
        else:
            r.validate_result(proposal, context)
        audit_and_save(root, ledger, state, paper, proposal, context, config, item["extraction_model"])


def replay_saved(artifact, base_commit, key, root=r.ROOT):
    """Correct a previously held draft using Claude, then request a fresh audit."""
    verify_baseline(root, base_commit)
    config = r.read_json(root / "research/config.json")
    r.check_config(config)
    if config.get("approval_policy") != "claude_only":
        raise ValueError("Claude-only policy required")
    ledger = r.read_json(root / "research/proposals.json")
    old = ledger["proposals"][key]
    if old["status"] != "needs_evidence":
        raise ValueError("Only an unapplied, held candidate can be replayed")
    paths = list(artifact.rglob(f"{key}-extract.jsonl"))
    if len(paths) != 1:
        raise ValueError("Missing or ambiguous original draft")
    record = json.loads(paths[0].read_text().splitlines()[-1])
    if record["model"] != old["extraction_model"] or record["id"] != key:
        raise ValueError("Original draft provenance mismatch")
    source = load_evidence(paths[0], old)
    draft, _ = correct_pages(json.loads(record["response"]), source["pages"])
    state = r.load_state(root / "new-papers.json")
    paper = next(p for p in state["papers"] if p["arxiv_id"] == key)
    cards = [r.get_official_resource(url) for url in sorted({c["row"]["링크"] for c in draft["changes"]})]
    source["official_resources"] = [{k: v for k, v in c.items() if k != "text"} for c in cards]
    context = {"paper": {k: v for k, v in paper.items() if not k.startswith(("analysis_", "review_"))},
               "source": source, "official_resources": cards,
               "tables": {track: dict(zip(("headers", "rows"), r.read_table(root, track))) for track in r.TABLES},
               "english_copy": (root / "english-copy.js").read_text()}
    prompt = (r.PROMPT + "\nRevise the unverified draft below using ONLY supplied evidence. "
              "Remove unsupported usage-note claims, including assumptions that a repository has a code license. "
              "Unknown license status is allowed. Return the complete corrected proposal JSON.\n"
              + r.evidence_payload(context) + "\nUNVERIFIED DRAFT:\n" + json.dumps(draft, ensure_ascii=False))
    result = call(prompt, root / ".research-cache" / "claude" / key / "repair",
                  lambda text: r.validate_result(r.load_json_answer(text), context))
    proposal = {k: result[k] for k in ("decision", "reason", "changes")}
    if proposal["decision"] != "propose":
        print(f"{key}: Claude did not produce a supported proposal; existing held record retained")
        return
    # A revised official link needs a newly fetched card before the independent pass.
    cards = [r.get_official_resource(url) for url in sorted({c["row"]["링크"] for c in proposal["changes"]})]
    context["official_resources"] = cards
    source["official_resources"] = [{k: v for k, v in c.items() if k != "text"} for c in cards]
    audit_and_save(root, ledger, state, paper, proposal, context, config, MODEL)


def unhold(ledger, state, attempts, key):
    """Move a held/rejected/needs_evidence record to ledger['reaudits'] and queue the paper again."""
    item = ledger["proposals"].get(key)
    paper = next((p for p in state["papers"] if p["arxiv_id"] == key), None)
    if paper is None:
        raise ValueError("Re-audit candidate is not in new-papers.json")
    if item is not None and item.get("status") not in {"held", "rejected", "needs_evidence"}:
        raise ValueError("Only a held, rejected or needs_evidence candidate can be re-audited")
    if item is None and paper.get("analysis_status") not in {"held", "needs_evidence", "queued"}:
        raise ValueError("Only a held, rejected or needs_evidence candidate can be re-audited")
    if ledger.get("screenings", {}).get(key, {}).get("status") != "passed":
        raise ValueError("Re-audit needs a passed abstract screening")
    if item is not None:
        ledger.setdefault("reaudits", []).append({**item, "superseded_at": r.iso(datetime.now(timezone.utc))})
        del ledger["proposals"][key]
    attempts["attempted"] = [k for k in attempts["attempted"] if k != key]
    paper.update(analysis_status="queued", analysis_reason="현재 공개 기준으로 재심사 대기")
    return paper


def run(root=r.ROOT, dry_run=False, screening_smoke=False, reaudit=None):
    """Use subscription Claude for new abstracts, drafts and the final audit."""
    config = r.read_json(root / "research/config.json")
    r.check_config(config)
    if dry_run:
        print("Claude subscription pipeline: no call in dry-run mode")
        return
    ledger = r.read_json(root / "research/proposals.json")
    state = r.load_state(root / "new-papers.json")
    started = time.monotonic()
    deadline = started + config.get("run_minutes", 90) * 60
    day = datetime.now(timezone.utc).astimezone(r.KST).date().isoformat()
    attempts = ledger.setdefault("claude_daily_runs", {}).setdefault(day, {"attempted": [], "abstract_attempted": []})
    reaudit_paper = None
    if reaudit:
        pending = ledger["proposals"].get(reaudit)
        if pending and pending.get("status") == "awaiting_claude":
            # The draft already exists; finish its publication completion and audit
            # from the saved evidence instead of drafting again.
            resume_one(root, ledger, state, config, reaudit, pending)
            r.save_state(root / "new-papers.json", state)
            r.paid_call_checkpoint(root, ledger)
            return
        reaudit_paper = unhold(ledger, state, attempts, reaudit)
    # Preserve old provider stop flags; they are not Claude spending allowances.
    if not screening_smoke and not reaudit:
        resume_pending(root, ledger, state, config, deadline)
    screenings = ledger.setdefault("screenings", {})
    def cached(paper):
        previous = screenings.get(paper["arxiv_id"], {})
        # Reuse completed screening of unchanged text during the model migration.
        return (previous.get("paper_title") == paper["title"] and previous.get("abstract") == paper["summary"]
                and previous.get("status") in {"passed", "excluded"})
    pending = [p for p in reversed(state["papers"]) if p["arxiv_id"] not in ledger["proposals"] and not cached(p)]
    remaining = max(0, config.get("daily_abstracts", 1000) - len(attempts["abstract_attempted"]))
    pending = [] if reaudit else pending[:min(10, remaining) if screening_smoke else remaining]
    state["research"] = {"status": "screening", "last_run_at": r.iso(datetime.now(timezone.utc)),
                         "models": [MODEL], "policy": "claude_only"}
    screen_deadline = min(deadline, started + min(30, config.get("run_minutes", 90) / 2) * 60)
    size = config.get("abstract_batch_size", 20)
    for start in range(0, len(pending), size):
        if time.monotonic() >= screen_deadline:
            break
        batch = pending[start:start + size]
        ids = [p["arxiv_id"] for p in batch]
        prompt = r.SCREEN_PROMPT + "\n" + json.dumps([r.abstract_input(p) for p in batch], ensure_ascii=False)
        response = call(prompt, root / ".research-cache" / "claude" / "abstracts",
                        lambda text: {"papers": r.parse_screening(text, ids)})
        for paper in batch:
            key = paper["arxiv_id"]
            vote = {"model": MODEL, **response["papers"][key]}
            excluded = vote["decision"] == "irrelevant"
            screenings[key] = {"arxiv_id": key, "paper_title": paper["title"], "abstract": paper["summary"],
                               "paper_updated": paper["updated"], "created_at": r.iso(datetime.now(timezone.utc)),
                               "input_sha256": r.digest({"prompt": prompt, "model": MODEL}),
                               "version": "claude-v1", "policy": "claude_only",
                               "status": "excluded" if excluded else "passed", "votes": [vote]}
            paper.update(analysis_status="exclude" if excluded else "queued",
                         analysis_reason="Claude 초록 선별에서 제외" if excluded else "초록 선별 후 본문 조사 대기")
        attempts["abstract_attempted"].extend(ids)
        r.save_state(root / "new-papers.json", state)
        r.paid_call_checkpoint(root, ledger)
        print(f"Claude abstract screening: {start + len(batch)}/{len(pending)}", flush=True)
    if screening_smoke:
        state["research"]["status"] = "screened"
        r.save_state(root / "new-papers.json", state)
        return
    selected = [p for p in reversed(state["papers"]) if p["arxiv_id"] not in ledger["proposals"]
                and p["arxiv_id"] not in attempts["attempted"] and cached(p)
                and screenings[p["arxiv_id"]]["status"] == "passed"]
    selected = [reaudit_paper] if reaudit else selected[:max(0, config["daily_papers"] - len(attempts["attempted"]))]
    for paper in selected:
        if time.monotonic() >= deadline:
            break
        key = paper["arxiv_id"]
        attempts["attempted"].append(key)
        r.paid_call_checkpoint(root, ledger)
        try:
            source = r.get_pdf(key, root / ".research-cache" / day)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            paper.update(analysis_status="needs_evidence", analysis_reason="PDF 추출 실패, 다음 실행에서 재시도")
            print(f"{key}: PDF extraction failed: {str(error)[:300]}", flush=True)
            r.save_state(root / "new-papers.json", state)
            continue
        try:
            investigate(root, ledger, state, config, screenings, paper, source)
        except ValueError as error:
            # An empty or unparseable Claude answer skips this paper only. A saved
            # awaiting_claude record is resumed on the next run.
            paper.update(analysis_status="needs_evidence", analysis_reason=f"Claude 응답 처리 실패, 다음 실행에서 재시도: {str(error)[:200]}")
            print(f"{key}: Claude answer unusable, skipped: {str(error)[:300]}", flush=True)
        r.save_state(root / "new-papers.json", state)
        r.paid_call_checkpoint(root, ledger)
    state["research"].update(status="paused_time_budget" if time.monotonic() >= deadline else "ready",
                             abstract_screened_total=len(screenings), full_text_completed_total=len(ledger["proposals"]))
    r.save_state(root / "new-papers.json", state)


def investigate(root, ledger, state, config, screenings, paper, source):
    """Draft one paper's inventory change with Claude and hand it to the audit."""
    key = paper["arxiv_id"]
    if True:
        context = {"paper": {k: v for k, v in paper.items() if not k.startswith(("analysis_", "review_"))},
                   "source": source,
                   "allow_score_updates": config.get("publication_policy") == "complete-evidence-v1",
                   "tables": {track: dict(zip(("headers", "rows"), r.read_table(root, track))) for track in r.TABLES},
                   "english_copy": (root / "english-copy.js").read_text()}
        result = call(r.PROMPT + "\n" + r.evidence_payload(context),
                      root / ".research-cache" / "claude" / key / "draft",
                      lambda text: r.validate_result(r.load_json_answer(text), context))
        proposal = {k: result[k] for k in ("decision", "reason", "changes")}
        if proposal["decision"] == "propose":
            try:
                cards = [r.get_official_resource(url) for url in sorted({c["row"]["링크"] for c in proposal["changes"]})]
            except (OSError, ValueError, KeyError):
                # Transient card errors stay eligible tomorrow, not permanently excluded.
                paper.update(analysis_status="needs_evidence", analysis_reason="공식 자료 확인 실패, 다음 실행에서 재시도")
                r.save_state(root / "new-papers.json", state)
                return
            context["official_resources"] = cards
            source["official_resources"] = [{k: v for k, v in card.items() if k != "text"} for card in cards]
            audit_and_save(root, ledger, state, paper, proposal, context, config, MODEL)
        else:
            proposal.update(arxiv_id=key, paper_title=paper["title"], paper_updated=paper["updated"],
                            source={k: v for k, v in source.items() if k != "pages"},
                            status=proposal["decision"], created_at=r.iso(datetime.now(timezone.utc)),
                            extraction_model=MODEL, approval_policy="claude_only", screening=screenings[key], issue_url=None)
            proposal["proposal_sha256"] = r.digest({k: proposal[k] for k in ("arxiv_id", "changes", "source")})
            ledger["proposals"][key] = proposal
            paper.update(analysis_status=proposal["status"], analysis_reason=proposal["reason"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--base-commit")
    parser.add_argument("--key")
    parser.add_argument("--reaudit", metavar="ARXIV_ID")
    args = parser.parse_args()
    config = r.read_json(r.ROOT / "research/config.json")
    r.check_config(config)
    if args.resume:
        resume_pending(r.ROOT, r.read_json(r.ROOT / "research/proposals.json"),
                       r.load_state(r.ROOT / "new-papers.json"), config, time.monotonic() + 3600)
    elif args.artifact and args.base_commit and args.key:
        replay_saved(args.artifact, args.base_commit, args.key)
    else:
        parser.error("Use --resume or --artifact, --base-commit and --key")

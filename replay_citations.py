"""Re-audit at most ten saved drafts after uniquely locating exact PDF quotes.

No discovery, PDF extraction, or draft generation. All existing content checks
and both independent model votes are still required before inventory application.
"""
import argparse
import copy
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import research_pipeline as r


def correct_pages(result, pages):
    result = copy.deepcopy(result)
    repairs = []
    for change in result.get("changes", []):
        for field, value in change.get("evidence", {}).items():
            ev = value[0] if isinstance(value, list) and len(value) == 1 else value
            if not isinstance(ev, dict) or type(ev.get("page")) is not int or not isinstance(ev.get("quote"), str):
                continue
            page, quote = ev["page"], r.compact(ev["quote"])
            if not quote or (1 <= page <= len(pages) and quote in r.compact(pages[page - 1])):
                continue
            matches = [i + 1 for i, text in enumerate(pages) if quote in r.compact(text)]
            if len(matches) == 1:
                ev["page"] = matches[0]
                repairs.append({"track": change["track"], "field": field, "from_page": page,
                                "to_page": matches[0], "quote_sha256": r.digest(ev["quote"])})
    return result, repairs


def verify_baseline(root, commit):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("A source-run commit SHA is required")
    for name in list(r.TABLES.values()) + ["english-copy.js", "benchmark-modalities.json"]:
        before = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=root)
        if before != (root / name).read_bytes():
            raise ValueError(f"Inventory changed since draft generation: {name}")


def load_evidence(path, old):
    key = old["arxiv_id"]
    pdf = path.with_name(f"{key}.pdf")
    page_file = path.with_name(f"{key}.pages.json")
    source = copy.deepcopy(old["source"])
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError("Original PDF hash mismatch")
    if hashlib.sha256(page_file.read_bytes()).hexdigest() != source["extraction"]["page_json_sha256"]:
        raise ValueError("Page JSON hash mismatch")
    document = r.read_json(page_file)
    records = document["pages"]
    if [x["page"] for x in records] != list(range(1, len(records) + 1)):
        raise ValueError("Physical page sequence changed")
    source["pages"] = [x["text"] for x in records]
    return source


def run(artifact, base_commit, source_run, root=r.ROOT, dry_run=False):
    if not re.fullmatch(r"[0-9]+", source_run):
        raise ValueError("Invalid source run ID")
    verify_baseline(root, base_commit)
    config = r.read_json(root / "research/config.json")
    r.check_config(config)
    if not config.get("enabled") or not config.get("auto_apply_agreed") or config["model"] == config.get("verifier_model"):
        raise ValueError("Replay requires enabled two-model automatic verification")
    ledger = r.read_json(root / "research/proposals.json")
    if any(day.get("blocked") for day in ledger.get("daily_runs", {}).values()):
        raise RuntimeError("Resolve the existing model-call checkpoint before replay")
    state = r.load_state(root / "new-papers.json")
    tables = {track: dict(zip(("headers", "rows"), r.read_table(root, track))) for track in r.TABLES}
    ready, report, seen = [], [], set()
    for path in sorted(artifact.rglob("*-extract.jsonl")):
        record = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
        key = record["id"]
        old = ledger["proposals"].get(key, {})
        if old.get("status") != "needs_evidence" or old.get("citation_replay") or "Quote does not occur" not in old.get("validation_error", ""):
            continue
        if key in seen:
            raise ValueError("Ambiguous duplicate source response")
        seen.add(key)
        try:
            if record.get("model") != old.get("extraction_model") or record.get("error") != old.get("validation_error"):
                raise ValueError("Saved response provenance mismatch")
            source = load_evidence(path, old)
            raw = json.loads(record["response"])
            fixed, repairs = correct_pages(raw, source["pages"])
            if not repairs:
                raise ValueError("No uniquely locatable page correction")
            paper = next(p for p in state["papers"] if p["arxiv_id"] == key)
            # Historical decisions and other votes are not supplied to auditors.
            bibliography = {k: v for k, v in paper.items() if not k.startswith(("analysis_", "review_"))}
            context = {"paper": bibliography, "source": source, "tables": tables,
                       "english_copy": (root / "english-copy.js").read_text()}
            proposal = r.validate_result(fixed, context)
            if proposal["decision"] != "propose":
                raise ValueError("Saved response does not propose an inventory change")
            ready.append((key, old, proposal, context, repairs))
            report.append({"arxiv_id": key, "status": "ready", "page_corrections": repairs})
        except (ValueError, KeyError, TypeError, OSError, StopIteration) as error:
            report.append({"arxiv_id": key, "status": "held", "reason": str(error)[:300]})
    folder = root / ".research-cache" / "citation-replay" / source_run
    folder.mkdir(parents=True, exist_ok=True)
    r.write_json(folder / "replay-report.json", report)
    print(f"Saved-draft replay: {len(ready)} ready; {len(report) - len(ready)} held; at most 10 papers")
    if dry_run or not ready:
        return report
    primary = r.provider(config)
    secondary = r.provider(config, config["verifier_model"])
    day = datetime.now(timezone.utc).astimezone(r.KST).date().isoformat()
    attempts = ledger.setdefault("daily_runs", {}).setdefault(day, {"attempted": [], "spent_usd": 0})
    for key, old, proposal, context, repairs in ready[:10]:
        if key not in attempts["attempted"] and len(attempts["attempted"]) >= config["daily_papers"]:
            break
        try:
            cards = [r.get_official_resource(url) for url in sorted({c["row"]["링크"] for c in proposal["changes"]})]
        except (OSError, ValueError, KeyError) as error:
            print(f"{key}: official source unavailable ({type(error).__name__}); held")
            continue
        context["official_resources"] = cards
        context["source"]["official_resources"] = [{k: v for k, v in card.items() if k != "text"} for card in cards]
        payload = r.evidence_payload(context) + "\nPROPOSAL:\n" + json.dumps(proposal, ensure_ascii=False)
        replay = {"source_run": source_run, "original_created_at": old["created_at"],
                  "page_corrections": repairs, "status": "auditing"}
        old["citation_replay"] = replay
        if key not in attempts["attempted"]:
            attempts["attempted"].append(key)
        attempts["blocked"] = True
        r.paid_call_checkpoint(root, ledger)
        votes = []
        for index, model in enumerate((primary, secondary)):
            job = {"id": f"{key}-replay-{r.digest(payload)[:12]}-{index}",
                   "messages": [{"role": "system", "content": r.VERIFY_PROMPT}, {"role": "user", "content": payload}]}
            try:
                vote, spent = r.invoke(job, model, folder / f"{job['id']}.jsonl", r.parse_check,
                                       config["cost_cap_usd"] - attempts["spent_usd"])
            except r.EvidenceRejected as error:
                spent = error.spent
                vote = {"approve": False, "reason": "근거 대조 응답의 형식 검사를 통과하지 못했습니다."}
            attempts["spent_usd"] += spent
            votes.append({"model": model.model, **vote})
        approved = all(v["approve"] for v in votes)
        if not approved:
            proposal.update(decision="needs_evidence", changes=[],
                            reason="페이지 위치 보정 후 두 모델의 검증을 통과하지 못했습니다: " + "; ".join(v["reason"] for v in votes if not v["approve"])[:1100])
        replay["status"] = "completed"
        proposal.update(arxiv_id=key, paper_title=old["paper_title"], paper_updated=old["paper_updated"],
                        source={k: v for k, v in context["source"].items() if k != "pages"},
                        created_at=r.iso(datetime.now(timezone.utc)), extraction_model=old["extraction_model"],
                        screening=old.get("screening"), issue_url=None, citation_replay=replay,
                        status="proposed" if approved else "needs_evidence", verification={"approve": approved, "votes": votes})
        proposal["proposal_sha256"] = r.digest({k: proposal[k] for k in ("arxiv_id", "changes", "source")})
        if approved:
            proposal["verification"]["reviewed_sha256"] = proposal["proposal_sha256"]
        ledger["proposals"][key] = proposal
        paper = next(p for p in state["papers"] if p["arxiv_id"] == key)
        paper.update(analysis_status=proposal["status"], analysis_reason=proposal["reason"])
        attempts["blocked"] = False
        r.write_json(root / "research/proposals.json", ledger)
        r.save_state(root / "new-papers.json", state)
        print(f"{key}: citation replay {proposal['status']}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--base-commit", required=True)
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args.artifact, args.base_commit, args.source_run, dry_run=args.dry_run)

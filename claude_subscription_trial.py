"""Prepare one saved-paper audit and validate official Claude Code output.

This trial never changes inventory or research decisions. Subscription credentials
belong only to the official action, not this evidence/response adapter.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import research_pipeline as r
from replay_citations import correct_pages, load_evidence, verify_baseline

KEY = "2510.26238"
MODEL = "claude-sonnet-5-5"
FOLDER = Path(".research-cache/claude-trial")


def prepare(artifact, base_commit, root=r.ROOT):
    verify_baseline(root, base_commit)
    old = r.read_json(root / "research/proposals.json")["proposals"][KEY]
    if old["status"] != "needs_evidence":
        raise ValueError("Trial requires the saved, unapplied QASU candidate")
    paths = list(artifact.rglob(f"{KEY}-extract.jsonl"))
    if len(paths) != 1:
        raise ValueError("Missing or ambiguous original draft")
    record = json.loads(paths[0].read_text().splitlines()[-1])
    if record["id"] != KEY or record["model"] != old["extraction_model"]:
        raise ValueError("Draft provenance mismatch")
    source = load_evidence(paths[0], old)
    fixed, repairs = correct_pages(json.loads(record["response"]), source["pages"])
    paper = next(p for p in r.load_state(root / "new-papers.json")["papers"] if p["arxiv_id"] == KEY)
    context = {
        "paper": {k: v for k, v in paper.items() if not k.startswith(("analysis_", "review_"))},
        "source": source,
        "tables": {track: dict(zip(("headers", "rows"), r.read_table(root, track))) for track in r.TABLES},
        "english_copy": (root / "english-copy.js").read_text(),
    }
    proposal = r.validate_result(fixed, context)
    if proposal["decision"] != "propose":
        raise ValueError("No validated draft")
    cards = [r.get_official_resource(url) for url in sorted({c["row"]["링크"] for c in proposal["changes"]})]
    context["official_resources"] = cards
    # All previous votes are deliberately absent.
    prompt = r.VERIFY_PROMPT + "\n\n" + r.evidence_payload(context) + "\nPROPOSAL:\n" + json.dumps(proposal, ensure_ascii=False)
    folder = root / FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "prompt.txt").write_text(prompt)
    manifest = {
        "arxiv_id": KEY, "model": MODEL, "base_commit": base_commit,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "draft_sha256": r.digest(proposal), "pdf_sha256": source["sha256"],
        "page_json_sha256": source["extraction"]["page_json_sha256"],
        "page_corrections": repairs,
        "official_resources": [{k: v for k, v in c.items() if k != "text"} for c in cards],
    }
    r.write_json(folder / "manifest.json", manifest)
    print(f"Prepared {KEY}; {len(prompt)} characters; no model call or inventory edit")
    return manifest


def parse_execution(messages):
    if not isinstance(messages, list) or not all(isinstance(m, dict) for m in messages):
        raise ValueError("Invalid execution log")
    init = [m for m in messages if m.get("type") == "system" and m.get("subtype") == "init"]
    results = [m for m in messages if m.get("type") == "result"]
    if len(init) != 1 or init[0].get("model") != MODEL or len(results) != 1:
        raise ValueError("Missing result or unexpected Claude model")
    result = results[0]
    if result.get("subtype") != "success" or result.get("is_error") is not False:
        raise ValueError("Claude request failed; keep the candidate pending")
    if type(result.get("num_turns")) is not int or not 1 <= result["num_turns"] <= 2:
        raise ValueError("Unexpected number of turns")
    if result.get("permission_denials"):
        raise ValueError("The audit attempted an unauthorized tool")
    for message in messages:
        content = message.get("message", {}).get("content", [])
        if isinstance(content, list) and any(isinstance(c, dict) and c.get("type") == "tool_use" for c in content):
            raise ValueError("The audit must not use tools")
    return {"model": MODEL, **r.parse_check(result.get("result", "")),
            "num_turns": result["num_turns"], "usage": result.get("usage", {})}


def consume(execution, root=r.ROOT):
    folder = root / FOLDER
    manifest = r.read_json(folder / "manifest.json")
    if hashlib.sha256((folder / "prompt.txt").read_bytes()).hexdigest() != manifest["prompt_sha256"]:
        raise ValueError("Audit input changed")
    messages = r.read_json(execution)
    try:
        result = parse_execution(messages)
    except (ValueError, KeyError, TypeError) as error:
        r.write_json(folder / "report.json", {
            **manifest, "trial_only": True, "inventory_applied": False,
            "error": str(error)[:500], "status": "invalid_response",
            "result_messages": [m for m in (messages if isinstance(messages, list) else [])
                                if isinstance(m, dict) and m.get("type") == "result"],
        })
        raise
    report = {**manifest, "verification": result, "trial_only": True, "inventory_applied": False,
              "created_at": r.iso(datetime.now(timezone.utc)), "run_id": os.environ.get("GITHUB_RUN_ID")}
    r.write_json(folder / "report.json", report)
    print(json.dumps({"arxiv_id": KEY, "approve": result["approve"], "reason": result["reason"],
                      "inventory_applied": False}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--artifact", type=Path, required=True)
    prep.add_argument("--base-commit", required=True)
    read = sub.add_parser("consume")
    read.add_argument("--execution", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.artifact, args.base_commit)
    else:
        consume(args.execution)

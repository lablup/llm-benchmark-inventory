#!/usr/bin/env python3
"""Archive unapplied research snapshots and publish only applied inventory updates."""
from __future__ import annotations

import html
import re
from pathlib import Path

from arxiv_watch import ROOT, KST, ARXIV_ID, timestamp
from research_pipeline import digest, read_json, write_json

ARCHIVED = {"exclude", "needs_evidence", "held", "rejected", "proposed"}
LABELS = {"exclude": "자동 조사에서 제외", "needs_evidence": "근거·판단 부족으로 미반영",
          "held": "보류", "rejected": "제외", "proposed": "변경안 작성, 아직 미반영"}


def prose(value):
    """Render model text as text, not GitHub Markdown/HTML instructions."""
    return re.sub(r"([\\`*_{}\[\]#!|>])", r"\\\1", html.escape(str(value), quote=False))


def archive_item(root, item):
    key = item["arxiv_id"]
    if not re.fullmatch(ARXIV_ID, key):
        raise ValueError("Invalid archive arXiv ID")
    date = timestamp(item["created_at"]).astimezone(KST)
    snapshot = {k: item.get(k) for k in ("arxiv_id", "paper_title", "created_at", "status", "reason",
                "source", "extraction_model", "verification", "validation_error", "proposal_sha256", "changes")}
    if "screening" in item:
        snapshot["screening"] = item["screening"]
    if item.get("approval_policy"):
        snapshot["approval_policy"] = item["approval_policy"]
    fingerprint = digest(snapshot)
    folder = root / "research/archive" / date.strftime("%Y-%m")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{key}-{date:%Y%m%dT%H%M%S}-{fingerprint[:12]}.md"
    lines = [f"# {prose(item['paper_title'])}", "", f"- 논문: https://arxiv.org/abs/{key}",
             f"- 조사 시각: {date:%Y-%m-%d %H:%M:%S} (한국 시간)",
             f"- 처리 상태: {LABELS[item['status']]}",
             f"- 1차 추출 모델: {prose(item.get('extraction_model') or '당시 기록에 모델명이 없음')}",
             "", "## 미반영 사유", "", prose(item.get("reason", "사유 기록 없음")), "",
             "이 사유는 당시 자동 조사 기록이며, 논문 자체의 부적합을 확정하는 판단이 아닙니다.",
             "", "## 모델의 근거 대조", ""]
    votes = item.get("verification", {}).get("votes", [])
    if votes:
        for vote in votes:
            lines += [f"- {prose(vote['model'])}: {'동의' if vote['approve'] else '미동의'}. {prose(vote['reason'])}"]
    elif item.get("approval_policy") == "claude_only":
        lines += ["Claude의 본문 승인 전에 종료된 조사입니다."]
    else:
        lines += ["두 모델의 교차 확인 기록이 없습니다. 1차 조사에서 종료된 결과를 두 모델의 합의로 해석하지 않습니다."]
    if item.get("validation_error"):
        lines += ["", "검사 오류: " + prose(item["validation_error"])]
    lines += ["", "## 근거 기록", "",
              f"- PDF 확인 시각: {prose(item.get('source', {}).get('accessed', '기록 없음'))}",
              f"- [상세 조사 기록(JSON)]({path.with_suffix('.json').name})",
              f"- PDF: https://arxiv.org/pdf/{key}",
              f"- PDF SHA-256: `{item.get('source', {}).get('sha256', '기록 없음')}`",
              f"- 조사 결과 SHA-256: `{item.get('proposal_sha256', '기록 없음')}`",
              f"- 보관 기록 SHA-256: `{fingerprint}`", ""]
    content = "\n".join(lines)
    if path.exists() and path.read_text(encoding="utf-8") != content:
        raise ValueError(f"Archive snapshot was modified: {path.name}")
    if not path.exists():
        path.write_text(content, encoding="utf-8")
    detail = path.with_suffix(".json")
    if detail.exists() and read_json(detail) != snapshot:
        raise ValueError(f"Archive snapshot was modified: {detail.name}")
    if not detail.exists():
        write_json(detail, snapshot)


def archive_screening(root, item):
    """Keep abstract-only exclusions visibly separate from PDF investigations."""
    key = item["arxiv_id"]
    if not re.fullmatch(ARXIV_ID, key):
        raise ValueError("Invalid archive arXiv ID")
    date = timestamp(item["created_at"]).astimezone(KST)
    fingerprint = digest(item)
    folder = root / "research/archive" / date.strftime("%Y-%m")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{key}-abstract-{date:%Y%m%dT%H%M%S}-{fingerprint[:12]}.md"
    lines = [f"# {prose(item['paper_title'])}", "", f"- 논문: https://arxiv.org/abs/{key}",
             f"- 초록 선별 시각: {date:%Y-%m-%d %H:%M:%S} (한국 시간)",
             "- 처리 단계: 초록 선별에서 제외, PDF 본문은 읽지 않음", "",
             ("Claude가 초록에서 관련성이 낮다고 판단한 기록이며, 본문 근거 검증을 마친 결과가 아닙니다."
              if item.get("policy") == "claude_only" else
              "두 모델이 초록에서 관련성이 낮다고 판단한 기록이며, 본문 근거 검증을 마친 결과가 아닙니다."),
             "", "## 초록 선별 결과", ""]
    for vote in item["votes"]:
        lines.append(f"- {prose(vote['model'])}: {prose(vote['decision'])}. {prose(vote['reason'])}")
    lines += ["", f"- [초록과 판정 기록(JSON)]({path.with_suffix('.json').name})",
              f"- 보관 기록 SHA-256: `{fingerprint}`", ""]
    content = "\n".join(lines)
    if path.exists() and path.read_text(encoding="utf-8") != content:
        raise ValueError(f"Archive snapshot was modified: {path.name}")
    if not path.exists():
        path.write_text(content, encoding="utf-8")
    detail = path.with_suffix(".json")
    if detail.exists() and read_json(detail) != item:
        raise ValueError(f"Archive snapshot was modified: {detail.name}")
    if not detail.exists():
        write_json(detail, item)


def build(root: Path = ROOT):
    state = read_json(root / "new-papers.json")
    ledger = read_json(root / "research/proposals.json")
    updates = []
    for item in ledger.get("screenings", {}).values():
        if item["status"] == "excluded":
            archive_screening(root, item)
    for item in ledger["proposals"].values():
        if item["status"] in ARCHIVED:
            archive_item(root, item)
        if item["status"] != "accepted":
            continue
        changes = []
        for change in item["changes"]:
            row, before = change["row"], change["before"]
            page = "korean.html" if change["track"] == "ko" else "english.html"
            modality = "?modality=vision" if change["modality"] == "vision" else ""
            fields = [field for field in row if before is not None and before.get(field) != row[field]]
            if before is not None and change.get("recommendations"):
                fields.append("추천 모델·평가 점수")
            labels = {"정의": "벤치마크 설명", "링크": "자료 링크", "대표 과제": "평가 과제",
                      "대표 예시·설명": "평가 예시", "예시 표기": "예시 표기", "이름": "벤치마크 이름"}
            if before is None:
                track = "한국어" if change["track"] == "ko" else "영어"
                axis = row.get("평가 축", "").strip()
                summary = f"{track} {axis + ' ' if axis else ''}평가 항목으로 새로 등록했습니다."
            else:
                summary = "변경한 내용: " + ", ".join(labels.get(field, field) for field in fields) + "."
            changes.append({"name": row["이름"], "action": "added" if before is None else "updated",
                            "summary": summary, "fields": fields,
                            "inventory_url": f"./{page}{modality}#inventory"})
        updates.append({"arxiv_id": item["arxiv_id"], "title": item["paper_title"],
                        "applied_at": item.get("applied_at"), "changes": changes,
                        "issue_url": item.get("issue_url")})
    updates.sort(key=lambda x: (x["applied_at"] or "", x["arxiv_id"]), reverse=True)
    write_json(root / "updates.json", {"schema_version": 1, "last_checked_at": state.get("last_checked_at"),
               "last_updated_at": max((u["applied_at"] for u in updates if u["applied_at"]), default=None),
               "updates": updates})
    archive = root / "research/archive"
    archive.mkdir(parents=True, exist_ok=True)
    months = sorted((p for p in archive.iterdir() if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}", p.name)), reverse=True)
    for folder in months:
        lines = [f"# {folder.name} 미반영 논문 조사 기록", "",
                 "조사 시각의 한국 시간 기준으로 보관합니다. 재조사 결과는 새 파일에 쌓이며 기존 기록은 유지합니다.", ""]
        for record in sorted(folder.glob("*.md"), reverse=True):
            if record.name == "README.md":
                continue
            title = record.read_text(encoding="utf-8").splitlines()[0].removeprefix("# ")
            lines.append(f"- [{record.name.split('-')[0]} · {title}]({record.name})")
        (folder / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (archive / "README.md").write_text("\n".join([
        "# 미반영 논문 조사 기록", "", "웹페이지에는 실제로 표에 반영한 변경만 표시합니다.",
        "제외·근거 부족·보류 등 미반영 결과는 조사월별로 보관합니다. 자동 조사 사유는 확정적인 부적합 판정이 아닙니다.",
        "아직 조사하지 않은 후보는 저장소의 `new-papers.json`에 있으며, 제외 기록으로 분류하지 않습니다.",
        "기존 기록의 모델명을 현재 설정으로 추정하지 않습니다. 이후 조사부터 실제 추출 모델명을 함께 기록합니다.", "",
        *[f"- [{folder.name}]({folder.name}/)" for folder in months], ""
    ]), encoding="utf-8")
    return updates


if __name__ == "__main__":
    print(f"Published {len(build())} applied updates and refreshed monthly research archives.")

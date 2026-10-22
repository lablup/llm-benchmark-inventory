"""Physical-page evidence from Poppler, with a bounded MinerU CPU fallback."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

MINERU_VERSION = "2.7.6"
MODEL_REVISION = "ed6b654c018d742e65a17671e379c5e6ecc87ec9"
MAX_PAGES = 60
MAX_CHARS = 200_000
MINERU_TIMEOUT = 600


def save_json(path: Path, value) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def fallback_reasons(pages: list[str]) -> list[str]:
    """Conservative layout heuristics, not a claim of complete table detection."""
    reasons = set()
    for page in pages:
        if len(page.strip()) < 40 or "\ufffd" in page or "(cid:" in page:
            reasons.add("sparse_or_broken_text")
        numeric_rows = sum(len(re.findall(r"\b\d+(?:\.\d+)?\b", line)) >= 3
                           and len(re.split(r"\s{2,}", line.strip())) >= 3
                           for line in page.splitlines())
        if numeric_rows >= 3 or re.search(r"(?im)^\s*(?:Table\s+\d+|표\s*\d+)", page):
            reasons.add("table_layout")
    return sorted(reasons)


def parse_mineru(items: list, page_count: int) -> list[list[dict]]:
    if not isinstance(items, list) or not items:
        raise ValueError("Empty MinerU content list")
    pages = [[] for _ in range(page_count)]
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Invalid MinerU block")
        index = item.get("page_idx")
        if type(index) is not int or not 0 <= index < page_count:
            raise ValueError("MinerU physical page index is invalid")
        block = {key: item[key] for key in ("type", "text", "text_format", "bbox",
                 "table_body", "table_caption", "table_footnote", "image_caption",
                 "image_footnote") if key in item}
        if block.get("type") == "table" and not block.get("table_body", "").strip():
            # One unparsed table no longer discards the whole paper: the page keeps
            # its Poppler text and the gap is marked so auditors do not trust a
            # silent omission.
            block["table_body"] = "[MinerU could not parse this table; use the original PDF text below]"
            block["table_missing"] = True
        pages[index].append(block)
    return pages


def block_text(block: dict) -> str:
    pieces = []
    for key in ("text", "table_caption", "table_body", "table_footnote", "image_caption", "image_footnote"):
        value = block.get(key, "")
        if isinstance(value, list) and all(isinstance(part, str) for part in value):
            pieces.extend(value)
        elif isinstance(value, str):
            pieces.append(value)
        else:
            raise ValueError("Unexpected MinerU text field")
    return "\n".join(filter(None, pieces))


def extract_pdf(pdf: Path, *, force_mineru: bool = False) -> dict:
    """Keep the PDF and page JSON together; never use a partial failed extraction."""
    started = time.monotonic()
    pdf_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()
    info = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True,
                          text=True, timeout=30).stdout
    match = re.search(r"(?m)^Pages:\s+(\d+)", info)
    if not match or not 1 <= int(match[1]) <= MAX_PAGES:
        raise ValueError("PDF exceeds the physical page limit")
    count = int(match[1])
    poppler = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True, timeout=10)
    version = (poppler.stderr or poppler.stdout).splitlines()[0]
    text_path = pdf.with_suffix(".txt")
    reasons = []
    try:
        subprocess.run(["pdftotext", "-layout", str(pdf), str(text_path)], check=True, timeout=45)
        raw = text_path.read_text(encoding="utf-8").split("\f")
        if len(raw) == count + 1 and not raw[-1].strip():
            raw.pop()
        if len(raw) != count:
            raise ValueError("Poppler page count mismatch")
        reasons = fallback_reasons(raw)
    except (subprocess.SubprocessError, UnicodeError, ValueError):
        raw = [""] * count
        reasons = ["poppler_failed"]
    if sum(map(len, raw)) > MAX_CHARS:
        # The original text alone already exceeds the budget; skip the minutes of
        # MinerU work that cannot bring it back under the limit.
        raise ValueError("PDF evidence exceeds the context limit")
    if force_mineru:
        reasons.append("forced_smoke")
    records = [{"page": index + 1, "original_text": re.sub(r"[ \t]{2,}", " ", page), "blocks": []}
               for index, page in enumerate(raw)]
    backend = "poppler"
    if reasons:
        executable = os.environ.get("MINERU_BIN", "mineru")
        installed = subprocess.run([executable, "--version"], capture_output=True, text=True,
                                   check=True, timeout=30).stdout.strip()
        if not installed.endswith(f"version {MINERU_VERSION}"):
            raise ValueError("Unexpected MinerU version")
        with tempfile.TemporaryDirectory(prefix=f"{pdf.stem}-mineru-", dir=pdf.parent) as directory:
            output = Path(directory)
            language = "korean" if re.search(r"[가-힣]", "".join(raw)) else "en"
            command = [executable, "-p", str(pdf.resolve()), "-o", str(output.resolve()),
                       "-b", "pipeline", "-m", "auto", "-l", language, "-d", "cpu", "-t", "True", "-f", "False"]
            # Separate log avoids losing diagnostics or flooding the workflow console.
            with pdf.with_suffix(".mineru.log").open("w", encoding="utf-8") as log:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=MINERU_TIMEOUT)
            lists = list(output.glob(f"{pdf.stem}/*/{pdf.stem}_content_list.json"))
            middles = list(output.glob(f"{pdf.stem}/*/{pdf.stem}_middle.json"))
            if len(lists) != 1 or len(middles) != 1:
                raise ValueError("Missing or ambiguous MinerU output")
            middle = json.loads(middles[0].read_text())
            if not isinstance(middle, dict):
                raise ValueError("Invalid MinerU middle JSON")
            indices = [page.get("page_idx") for page in middle.get("pdf_info", [])]
            if indices != list(range(count)):
                raise ValueError("MinerU omitted or reordered physical pages")
            blocks = parse_mineru(json.loads(lists[0].read_text()), count)
            for record, page_blocks in zip(records, blocks):
                record["blocks"] = page_blocks
        backend = "mineru"
    def page_text(record, keep_original):
        extracted = "\n".join(block_text(block) for block in record["blocks"]).strip()
        if backend != "mineru":
            return record["original_text"]
        if keep_original:
            return f"MinerU text and table HTML:\n{extracted}\nOriginal PDF text (Poppler):\n{record['original_text']}"
        return f"MinerU text and table HTML:\n{extracted}"
    pages = [page_text(record, True) for record in records]
    reduced = False
    if backend == "mineru" and sum(map(len, pages)) > MAX_CHARS:
        # Both extractions of every page double the size. Keep the Poppler copy
        # only beside tables, where the audit compares the two, and drop it on
        # plain-text pages instead of discarding the paper.
        has_table = [any(block.get("type") == "table" for block in record["blocks"]) for record in records]
        pages = [page_text(record, keep) for record, keep in zip(records, has_table)]
        reduced = True
    for record, text in zip(records, pages):
        record["text"] = text
    if not any(record["original_text"].strip() or any(block_text(b).strip() for b in record["blocks"]) for record in records):
        raise ValueError("No usable PDF evidence")
    if sum(map(len, pages)) > MAX_CHARS:
        raise ValueError("PDF evidence exceeds the context limit")
    missing_tables = sum(block.get("table_missing") is True for record in records for block in record["blocks"])
    metadata = {"backend": backend, "poppler_version": version, "fallback_reasons": reasons,
                "page_count": count, "elapsed_seconds": round(time.monotonic() - started, 2),
                "pdf_sha256": pdf_hash, "visual_pdf_audit": False,
                "original_text_reduced": reduced, "tables_missing": missing_tables}
    if backend == "mineru":
        metadata.update(mineru_version=MINERU_VERSION, model_revision=os.environ.get("MINERU_MODEL_REVISION", "unverified"),
                        device="cpu", formula_recognition=False, language=language)
    target = pdf.with_suffix(".pages.json")
    save_json(target, {"schema_version": 1, "extraction": metadata, "pages": records})
    metadata["page_json_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    metadata["page_json_file"] = target.name
    print(f"{pdf.stem}: {backend}, {count} pages, {metadata['elapsed_seconds']}s, reasons={reasons}")
    return {"pages": pages, "page_numbers": list(range(1, count + 1)), "extraction": metadata}

#!/usr/bin/env python3
"""Validate the inventory CSV files, the English copy table, and the site pages.

Standard library only. Exits non-zero with a message on the first problem found.
"""
from __future__ import annotations

import csv
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
BENCHMARK_HEADERS = [
    "id", "이름", "평가 축", "언어", "정의", "대표 과제", "대표 예시·설명",
    "라이선스", "상업적 이용", "lm-eval 지원", "링크",
]
SERVING_HEADERS = [
    "id", "이름", "분류", "측정 대상", "주요 지표", "부하 방식", "하드웨어 공개",
    "원시 결과", "에어갭", "라이선스", "운영 상태", "최근 확인일", "Benchpress 판단", "설명", "링크",
]
SERVING_ENUMS = {
    "분류": ["측정 도구", "공개 성능 표준", "공개 성능 보드", "회귀 대시보드", "자원 계측"],
    "에어갭": ["가능", "조건부", "해당 없음"],
    "운영 상태": ["활성", "단계적 종료", "유지보수 확인 필요", "초기 공개"],
    "Benchpress 판단": ["사용 중", "도입 후보", "참고", "보류", "방법론 채택", "관찰", "도입 예정", "대체 수단"],
}
RECOMMENDED_HEADERS = [
    "benchmark_id", "benchmark_name", "track", "scope", "rank", "model", "model_url", "score", "open_weight",
    "metric", "setting", "source_type", "source_title", "source_url", "source_date", "evidence", "status", "accessed",
]
REQUIRED_PAGES = [
    "index.html", "korean.html", "english.html", "serving.html", "english-copy.js",
    "assets/landing-map-desktop.webp", "assets/landing-map-mobile.webp",
    "assets/landing-map-ko-desktop.webp", "assets/landing-map-ko-mobile.webp",
]


def abort(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def read_csv(name: str) -> tuple[list[str], list[dict]]:
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def blank(value) -> bool:
    return value is None or str(value).strip() == ""


def is_https(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_required(headers: list[str], rows: list[dict], name: str, required: list[str]) -> None:
    missing = [header for header in required if header not in headers]
    if missing:
        abort(f"{name}: missing headers: {', '.join(missing)}")
    for index, row in enumerate(rows):
        empty = [header for header in required if blank(row.get(header))]
        if empty:
            abort(f"{name}: row {index + 2} missing: {', '.join(empty)}")


def validate_ids(rows: list[dict], name: str) -> None:
    seen: dict[str, int] = {}
    for row in rows:
        seen[row["id"]] = seen.get(row["id"], 0) + 1
    duplicates = [key for key, count in seen.items() if count > 1]
    if duplicates:
        abort(f"{name}: duplicate ids: {', '.join(duplicates)}")


def validate_https_links(rows: list[dict], name: str) -> None:
    for index, row in enumerate(rows):
        public_link = re.split(r"\s+\(", str(row.get("링크") or ""), maxsplit=1)[0]
        if not is_https(public_link):
            abort(f"{name}: row {index + 2} link must use https")


def validate_enums(rows: list[dict], name: str, allowed_values: dict[str, list[str]]) -> None:
    for header, allowed in allowed_values.items():
        invalid = [f"row {index + 2}: {row.get(header)}" for index, row in enumerate(rows) if row.get(header) not in allowed]
        if invalid:
            abort(f"{name}: invalid {header}: {', '.join(invalid)}")


def validate_iso_date(value: str, name: str, line: int) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        abort(f"{name}: row {line}: {error}")


def main() -> None:
    benchmark_tables = {}
    for name in ["korean_benchmark_inventory.csv", "english_benchmark_inventory.csv"]:
        headers, rows = read_csv(name)
        validate_required(headers, rows, name, BENCHMARK_HEADERS)
        validate_ids(rows, name)
        validate_https_links(rows, name)
        benchmark_tables[name] = rows

    english_ids = [row["id"] for row in benchmark_tables["english_benchmark_inventory.csv"]]
    english_copy = (ROOT / "english-copy.js").read_text(encoding="utf-8")
    english_copy_ids = [quoted or bare for quoted, bare in re.findall(r'^  (?:"([^"]+)"|([a-z0-9]+)):\s*\{', english_copy, flags=re.MULTILINE)]
    missing_copy = [key for key in english_ids if key not in english_copy_ids]
    extra_copy = [key for key in english_copy_ids if key not in english_ids]
    if missing_copy:
        abort(f"english-copy.js: missing ids: {', '.join(missing_copy)}")
    if extra_copy:
        abort(f"english-copy.js: unknown ids: {', '.join(extra_copy)}")

    serving_headers, serving = read_csv("serving_inventory.csv")
    validate_required(serving_headers, serving, "serving_inventory.csv", SERVING_HEADERS)
    validate_ids(serving, "serving_inventory.csv")
    validate_https_links(serving, "serving_inventory.csv")
    validate_enums(serving, "serving_inventory.csv", SERVING_ENUMS)
    for index, row in enumerate(serving):
        validate_iso_date(row.get("최근 확인일"), "serving_inventory.csv", index + 2)

    recommended_path = ROOT / "benchmark_top_models.csv"
    if recommended_path.is_file():
        name = recommended_path.name
        headers, recommended = read_csv(name)
        missing = [header for header in RECOMMENDED_HEADERS if header not in headers]
        if missing:
            abort(f"{name}: missing headers: {', '.join(missing)}")
        known_ids = {row["id"] for rows in benchmark_tables.values() for row in rows}
        for index, row in enumerate(recommended):
            line = index + 2
            if row.get("benchmark_id") not in known_ids:
                abort(f"{name}: row {line}: unknown benchmark_id {row.get('benchmark_id')}")
            if row.get("scope") not in ("all", "open_weight"):
                abort(f"{name}: row {line}: scope must be all or open_weight")
            if str(row.get("rank")) not in ("1", "2", "3"):
                abort(f"{name}: row {line}: rank must be 1..3")
            if row.get("status") not in ("verified", "partial"):
                abort(f"{name}: row {line}: status must be verified or partial")
            if row.get("scope") == "open_weight" and str(row.get("open_weight")).lower() != "true":
                abort(f"{name}: row {line}: open_weight scope requires open_weight=true")
            for header in ["model", "score", "source_url", "source_date", "accessed"]:
                if blank(row.get(header)):
                    abort(f"{name}: row {line}: missing {header}")
            if not is_https(row["source_url"]):
                abort(f"{name}: row {line}: source_url must use https")
            for header in ["model_url", "ow_source_url"]:
                if not blank(row.get(header)) and not is_https(row[header]):
                    abort(f"{name}: row {line}: {header} must use https")
            validate_iso_date(row["accessed"], name, line)
        print(f"Validated {len(recommended)} recommended-model rows.")

    for name in REQUIRED_PAGES:
        if not (ROOT / name).is_file():
            abort(f"missing page: {name}")

    print(f"Validated 2 benchmark inventories and {len(serving)} serving records.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Normalize the benchmark CSV files (license judgment columns) and regenerate README.md.

Standard library only. Run after editing a benchmark CSV; then run build_site_data.py.
"""
from __future__ import annotations

import csv
import io
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LICENSE_CHECKED_ON = "2026-09-26"
MISSING_LICENSE_PATTERN = re.compile(r"미표기|미기재|미확인|미선언|미확정")
REVIEW_LICENSE_PATTERN = re.compile(r"충돌|확인 필요|비공개|공식 사이트|커스텀|AI-Hub|약정|카드 'cc'|LGPL-3\.0 태그")
KNOWN_LICENSE_PATTERN = re.compile(r"MIT|Apache-2\.0|CC-BY|CC BY|CC-BY-SA|CC BY-SA|CC-BY-ND|CC BY-ND")
NC_PATTERN = re.compile(r"NC(?:-| |$)|비상업", re.MULTILINE)
ND_PATTERN = re.compile(r"ND|무변형")
SA_PATTERN = re.compile(r"SA|동일조건")

FILES = {
    "korean_benchmark_inventory.csv": "한국어 벤치마크",
    "english_benchmark_inventory.csv": "영어 벤치마크",
}
OUTPUT_HEADERS = [
    "id", "이름", "평가 축", "언어", "정의", "대표 과제", "대표 예시·설명", "예시 표기",
    "라이선스", "상업적 이용", "수정·파생", "재배포", "이용 시 유의사항", "lm-eval 지원", "링크",
]
CATEGORY_RULES = [
    (re.compile(r"의료|법률"), "전문 도메인"),
    (re.compile(r"수학|추론|사고력|상식|ARC|추상"), "추론·수학"),
    (re.compile(r"코딩"), "코딩"),
    (re.compile(r"검색|RAG|장문"), "검색·RAG·장문"),
    (re.compile(r"안전|편향|유해|환각|사실성"), "안전·사실성"),
    (re.compile(r"에이전트|함수 호출|터미널|컴퓨터 사용"), "에이전트·도구 사용"),
    (re.compile(r"생성|judge|메타평가"), "생성·평가"),
    (re.compile(r"이해|언어|NLU|독해|문법|문장 의미|읽기"), "이해·언어"),
    (re.compile(r"지시이행"), "지시이행"),
]


def text_of(value) -> str:
    return "" if value is None else str(value)


def license_fields(row_id: str, license_text: str, caution: str) -> tuple[str, str, str, str]:
    text = f"{license_text} {caution}"
    if row_id == "frontiermath":
        return license_text, "조건 확인 필요", "접근 불가", "불가"
    if row_id == "k-halu":
        return license_text, "조건 확인 필요", "약정 확인", "제3자 재배포 불가"
    if row_id == "haerae":
        return license_text, "조건 확인 필요", "버전별 확인", "버전별 확인"
    if NC_PATTERN.search(text):
        if ND_PATTERN.search(text):
            modification = "불가"
        elif SA_PATTERN.search(text):
            modification = "가능(동일조건)"
        else:
            modification = "가능(조건 준수)"
        redistribution = "원본 그대로만" if ND_PATTERN.search(text) else "조건부 가능"
        return license_text, "불가", modification, redistribution
    if ND_PATTERN.search(text):
        commercial = "가능" if KNOWN_LICENSE_PATTERN.search(license_text) else "조건 확인 필요"
        return license_text, commercial, "불가", "원본 그대로만"
    if MISSING_LICENSE_PATTERN.search(license_text):
        return license_text, "확인 불가", "확인 불가", "확인 불가"
    if REVIEW_LICENSE_PATTERN.search(text) or row_id in ("ko-truthfulqa", "kosbi"):
        return license_text, "조건 확인 필요", "조건 확인 필요", "조건 확인 필요"
    if KNOWN_LICENSE_PATTERN.search(license_text):
        modification = "가능(동일조건)" if SA_PATTERN.search(text) else "가능(조건 준수)"
        return license_text, "가능", modification, "조건부 가능"
    return license_text, "조건 확인 필요", "조건 확인 필요", "조건 확인 필요"


def example_label(language: str, example: str) -> str:
    if language.startswith("ko"):
        return "한국어 예시·요약"
    korean_count = len(re.findall(r"[가-힣]", example))
    latin_count = len(re.findall(r"[A-Za-z]", example))
    return "영문 예시(한국어 주석)" if latin_count > korean_count * 2 else "한국어 번역·요약"


def read_and_normalize(name: str) -> list[dict]:
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as fh:
        raw_rows = [{key: (value if value != "" else None) for key, value in row.items()} for row in csv.DictReader(fh)]
    rows = []
    for row in raw_rows:
        example = row.get("대표 예시") or row.get("대표 예시·설명")
        license_text, commercial, modification, redistribution = license_fields(
            row["id"], text_of(row.get("라이선스")), text_of(row.get("이용 시 유의사항"))
        )
        rows.append({
            "id": row["id"],
            "이름": row.get("이름"),
            "평가 축": row.get("평가 축"),
            "언어": row.get("언어"),
            "정의": row.get("정의"),
            "대표 과제": row.get("대표 과제"),
            "대표 예시·설명": example,
            "예시 표기": example_label(text_of(row.get("언어")), text_of(example)),
            "라이선스": license_text,
            "상업적 이용": commercial,
            "수정·파생": modification,
            "재배포": redistribution,
            "이용 시 유의사항": row.get("이용 시 유의사항"),
            "lm-eval 지원": row.get("lm-eval 지원"),
            "링크": row.get("링크"),
        })
    return rows


def category_for(axis: str) -> str:
    for pattern, category in CATEGORY_RULES:
        if pattern.search(axis):
            return category
    return "기타"


def write_csv(name: str, rows: list[dict]) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(OUTPUT_HEADERS)
    for row in rows:
        writer.writerow([text_of(row.get(header)) for header in OUTPUT_HEADERS])
    (ROOT / name).write_bytes(b"\xef\xbb\xbf" + buffer.getvalue().encode("utf-8"))


def markdown_escape(text) -> str:
    return re.sub(r"\r?\n", "<br>", text_of(text).replace("|", "\\|"))


def public_url(raw_url) -> str:
    return re.split(r"\s+\(", text_of(raw_url), maxsplit=1)[0]


def summary_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["상업적 이용"]] = counts.get(row["상업적 이용"], 0) + 1
    return counts


README_HEAD = """# LLM 벤치마크 인벤토리

![도시와 네트워크를 표현한 파란색 배너](./assets/network.png)

공개 페이지는 한국어와 영어 LLM 벤치마크, 서빙 성능 도구, 공개 성능 비교, GPU·엔진 자원 계측 자료를 한국어로 정리합니다.
영어권 사용자를 위한 영어 인터페이스는 별도 페이지로 추후 제공합니다.

- [한국어 랜딩 페이지](https://lablup.github.io/llm-benchmark-inventory/)
- [한국어 텍스트 벤치마크](https://lablup.github.io/llm-benchmark-inventory/korean.html)
- [한국어 이미지 벤치마크](https://lablup.github.io/llm-benchmark-inventory/korean.html?modality=vision)
- [영어 텍스트 벤치마크](https://lablup.github.io/llm-benchmark-inventory/english.html)
- [영어 이미지 벤치마크](https://lablup.github.io/llm-benchmark-inventory/english.html?modality=vision)
- [서빙·자원 인벤토리](https://lablup.github.io/llm-benchmark-inventory/serving.html)
- [한국어 벤치마크 CSV](./korean_benchmark_inventory.csv)
- [영어 벤치마크 CSV](./english_benchmark_inventory.csv)
- [서빙·자원 CSV](./serving_inventory.csv)
- [한국어 이미지 벤치마크 조사와 등재 판단](./docs/korean-vision-benchmarks.md)
- [벤치마크별 추천 모델 CSV](./benchmark_top_models.csv)
- [벤치마크별 추천 모델 조사 기록](./docs/recommended-models.md)

## 분야 구분

- **한국어·영어 벤치마크**는 모델 능력(model capability)을 평가하는 데이터셋과 실행 도구를 다룹니다.
- **서빙·자원**은 지연 시간과 처리량을 재는 도구, 공개 성능 비교, GPU·엔진 계측을 다룹니다.
- 점수는 출처와 확인일을 함께 적습니다. 벤치마크 카드의 **추천 모델**은 한 출처·한 설정 안에서 점수가 높은 모델 3개와 공개 가중치(open-weight) 모델 3개를 점수, 모델 링크, 출처 링크, 기준일과 함께 보여줍니다. 서빙·자원 자료는 공식 방법론과 결과 페이지를 연결하고 재현 조건과 운영 상태를 기록합니다. 조사 방법과 한계는 [벤치마크별 추천 모델 조사 기록](./docs/recommended-models.md)에 있습니다.

## 읽는 방법

- **상업적 이용**은 데이터 카드 등에 표시된 라이선스를 기준으로 `가능`, `불가`, `확인 불가`, `조건 확인 필요`의 네 가지로 구분합니다.
- 라이선스는 {checked_on}에 각 데이터 카드와 저장소에서 확인했습니다. 이후 바뀔 수 있으므로 실제 이용 전에 원문을 다시 확인해야 합니다.
- **대표 예시**는 각 벤치마크의 실제 과제 문항입니다. 영어 벤치마크는 한국어 번역이나 요약을 제공하는 경우가 많으며, CSV의 `예시 표기` 열에서 영문 예시와 한국어 요약을 구분합니다.
- `lm-eval 지원`은 오픈소스 평가 프레임워크 [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness)(EleutherAI)에 해당 과제가 내장되어 있는지를 뜻합니다. 조사 시점 기준이며 최신 버전에서는 달라질 수 있습니다.

"""

README_TAIL = """## 데이터 열

| 열 | 설명 |
|---|---|
| `대표 예시·설명` | 실제 또는 대표적인 과제 예시, 번역·요약 설명 |
| `예시 표기` | 한국어 예시·요약, 한국어 번역·요약, 영문 예시(한국어 주석) 구분 |
| `라이선스` | 데이터 카드 또는 원 출처에 표시된 라이선스와 조사 메모 |
| `상업적 이용` | 선언된 라이선스를 기준으로 한 상업적 이용 판단 |
| `수정·파생` | 번역, 변형 및 파생 데이터 제작 가능 여부 |
| `재배포` | 원본 또는 변형본 재배포 가능 여부 |
| `이용 시 유의사항` | 게이트 접근, 원저작권, 실행 환경 및 평가상 주의점 |

## 기여 시 확인 사항

1. 데이터 카드와 공식 저장소의 라이선스를 우선 확인
2. 데이터 라이선스와 코드·평가 하니스 라이선스를 구분
3. 번역본·미러·수집물은 원본 라이선스가 자동 승계된다고 가정하지 않기
4. 라이선스 재확인 시 문서 상단의 확인 기준일을 갱신
"""


def render_readme(normalized: dict[str, list[dict]]) -> str:
    parts = [README_HEAD.format(checked_on=LICENSE_CHECKED_ON)]
    for name, title in FILES.items():
        rows = normalized[name]
        counts = summary_counts(rows)
        parts.append(f"## {title}\n\n")
        parts.append(
            f"총 {len(rows)}개 · 상업적 이용 가능 {counts.get('가능', 0)}개 · 불가 {counts.get('불가', 0)}개 · "
            f"확인 불가 {counts.get('확인 불가', 0)}개 · 조건 확인 필요 {counts.get('조건 확인 필요', 0)}개\n\n"
        )
        grouped: dict[str, list[dict]] = {}
        for row in rows:
            grouped.setdefault(category_for(text_of(row["평가 축"])), []).append(row)
        for category, category_rows in grouped.items():
            parts.append(f"### {category}\n\n")
            parts.append("| 벤치마크 | 평가 축 | 설명 | 대표 예시 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |\n")
            parts.append("|---|---|---|---|---|---|---|\n")
            for row in category_rows:
                link_name = f"[{markdown_escape(row['이름'])}]({public_url(row['링크'])})"
                license_info = "<br>".join(part for part in [
                    markdown_escape(row["라이선스"]),
                    f"수정·파생: {markdown_escape(row['수정·파생'])}",
                    f"재배포: {markdown_escape(row['재배포'])}",
                    markdown_escape(row["이용 시 유의사항"]),
                ] if part)
                example_info = "<br>".join(part for part in [
                    f"**{markdown_escape(row['대표 과제'])}**" if text_of(row["대표 과제"]) else "",
                    markdown_escape(row["대표 예시·설명"]),
                ] if part)
                parts.append(
                    f"| {link_name} | {markdown_escape(row['평가 축'])} | {markdown_escape(row['정의'])} | {example_info} "
                    f"| **{markdown_escape(row['상업적 이용'])}** | {license_info} | {markdown_escape(row['lm-eval 지원'])} |\n"
                )
            parts.append("\n")
    parts.append(README_TAIL)
    return "".join(parts)


def main() -> None:
    normalized = {name: read_and_normalize(name) for name in FILES}
    for name, rows in normalized.items():
        write_csv(name, rows)
    (ROOT / "README.md").write_text(render_readme(normalized), encoding="utf-8")
    print("Normalized", ", ".join(FILES), "and regenerated README.md.")


if __name__ == "__main__":
    main()

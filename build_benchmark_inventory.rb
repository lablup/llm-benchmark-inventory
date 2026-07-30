#!/usr/bin/env ruby
# frozen_string_literal: true

require "csv"

LICENSE_CHECKED_ON = "2026-07-28"
MISSING_LICENSE_PATTERN = /미표기|미기재|미확인|미선언|미확정/
REVIEW_LICENSE_PATTERN = /충돌|확인 필요|비공개|공식 사이트|커스텀|AI-Hub|약정|카드 'cc'|LGPL-3\.0 태그/
KNOWN_LICENSE_PATTERN = /MIT|Apache-2\.0|CC-BY|CC BY|CC-BY-SA|CC BY-SA|CC-BY-ND|CC BY-ND/

FILES = {
  "korean_benchmark_inventory.csv" => "한국어 벤치마크",
  "english_benchmark_inventory.csv" => "영어 벤치마크"
}.freeze

def license_fields(id, license, caution)
  text = "#{license} #{caution}"

  if id == "frontiermath"
    commercial = "조건 확인 필요"
    modification = "접근 불가"
    redistribution = "불가"
  elsif id == "k-halu"
    commercial = "조건 확인 필요"
    modification = "약정 확인"
    redistribution = "제3자 재배포 불가"
  elsif id == "haerae"
    commercial = "조건 확인 필요"
    modification = "버전별 확인"
    redistribution = "버전별 확인"
  elsif text.match?(/NC(?:-| |$)|비상업/)
    commercial = "불가"
    modification =
      if text.match?(/ND|무변형/)
        "불가"
      elsif text.match?(/SA|동일조건/)
        "가능(동일조건)"
      else
        "가능(조건 준수)"
      end
    redistribution = text.match?(/ND|무변형/) ? "원본 그대로만" : "조건부 가능"
  elsif text.match?(/ND|무변형/)
    commercial = license.match?(KNOWN_LICENSE_PATTERN) ? "가능" : "조건 확인 필요"
    modification = "불가"
    redistribution = "원본 그대로만"
  elsif license.match?(MISSING_LICENSE_PATTERN)
    commercial = "확인 불가"
    modification = "확인 불가"
    redistribution = "확인 불가"
  elsif text.match?(REVIEW_LICENSE_PATTERN) || id == "ko-truthfulqa" || id == "kosbi"
    commercial = "조건 확인 필요"
    modification = "조건 확인 필요"
    redistribution = "조건 확인 필요"
  elsif license.match?(KNOWN_LICENSE_PATTERN)
    commercial = "가능"
    modification = text.match?(/SA|동일조건/) ? "가능(동일조건)" : "가능(조건 준수)"
    redistribution = "조건부 가능"
  else
    commercial = "조건 확인 필요"
    modification = "조건 확인 필요"
    redistribution = "조건 확인 필요"
  end

  [license, commercial, modification, redistribution]
end

def example_label(language, example)
  return "한국어 예시·요약" if language.start_with?("ko")

  korean_count = example.scan(/[가-힣]/).length
  latin_count = example.scan(/[A-Za-z]/).length
  latin_count > korean_count * 2 ? "영문 예시(한국어 주석)" : "한국어 번역·요약"
end

def read_and_normalize(path)
  table = CSV.read(path, headers: true, encoding: "bom|utf-8")
  table.map do |row|
    example = row["대표 예시"] || row["대표 예시·설명"]
    license, commercial, modification, redistribution =
      license_fields(row["id"], row["라이선스"], row["이용 시 유의사항"])

    {
      "id" => row["id"],
      "이름" => row["이름"],
      "평가 축" => row["평가 축"],
      "언어" => row["언어"],
      "정의" => row["정의"],
      "대표 과제" => row["대표 과제"],
      "대표 예시·설명" => example,
      "예시 표기" => example_label(row["언어"], example.to_s),
      "라이선스" => license,
      "상업적 이용" => commercial,
      "수정·파생" => modification,
      "재배포" => redistribution,
      "이용 시 유의사항" => row["이용 시 유의사항"],
      "lm-eval 지원" => row["lm-eval 지원"],
      "링크" => row["링크"]
    }
  end
end

def category_for(axis)
  case axis
  when /의료|법률/
    "전문 도메인"
  when /수학|추론|사고력|상식|ARC|추상/
    "추론·수학"
  when /코딩/
    "코딩"
  when /검색|RAG|장문/
    "검색·RAG·장문"
  when /안전|편향|유해|환각|사실성/
    "안전·사실성"
  when /에이전트|함수 호출|터미널|컴퓨터 사용/
    "에이전트·도구 사용"
  when /생성|judge|메타평가/
    "생성·평가"
  when /이해|언어|NLU|독해|문법|문장 의미|읽기/
    "이해·언어"
  when /지시이행/
    "지시이행"
  else
    "기타"
  end
end

def write_csv(path, rows)
  headers = rows.first.keys
  content = CSV.generate(force_quotes: false) do |csv|
    csv << headers
    rows.each { |row| csv << headers.map { |header| row[header] } }
  end
  File.binwrite(path, "\xEF\xBB\xBF#{content}")
end

def markdown_escape(text)
  text.to_s.gsub("|", "\\|").gsub(/\r?\n/, "<br>")
end

def public_url(raw_url)
  raw_url.to_s.split(/\s+\(/, 2).first
end

def summary_counts(rows)
  rows.group_by { |row| row["상업적 이용"] }
      .transform_values(&:length)
end

normalized = {}
FILES.each_key do |path|
  normalized[path] = read_and_normalize(path)
  write_csv(path, normalized[path])
end

readme = []
readme << "# LLM 벤치마크 인벤토리"
readme << ""
readme << "![도시와 네트워크를 표현한 파란색 배너](./assets/network.png)"
readme << ""
readme << "한국어 및 영어 LLM 벤치마크의 평가 범위, 과제 예시, 라이선스와 실행 지원 정보를 정리한 목록."
readme << "이 문서는 빠른 탐색을 위한 요약이며, 전체 필드는 원본 CSV에서 확인 가능"
readme << ""
readme << "- [한국어 벤치마크 CSV](./korean_benchmark_inventory.csv)"
readme << "- [영어 벤치마크 CSV](./english_benchmark_inventory.csv)"
readme << ""
readme << "## 읽는 방법"
readme << ""
readme << "- **상업적 이용**은 데이터 카드 등에 표시된 라이선스를 기준으로 `가능`, `불가`, `확인 불가`, `조건 확인 필요`의 네 가지로 구분"
readme << "- 라이선스는 #{LICENSE_CHECKED_ON}에 각 데이터 카드와 저장소에서 일괄 확인한 것. 이후 바뀔 수 있으므로 실제 이용 전 원문 재확인 필요"
readme << "- **대표 예시**는 각 벤치마크의 실제 과제 문항. 영어 벤치마크의 예시는 한국어 독자를 위한 번역·요약이 많으며, CSV의 `예시 표기` 열로 영문 예시와 한국어 요약을 구분"
readme << "- `lm-eval 지원`은 오픈소스 평가 프레임워크 [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness)(EleutherAI)에 해당 태스크가 내장돼 있는지 여부. 인벤토리 작성 시점 기준이며 최신 버전에서 달라질 수 있음"
readme << ""

FILES.each do |path, title|
  rows = normalized[path]
  counts = summary_counts(rows)
  readme << "## #{title}"
  readme << ""
  readme << "총 #{rows.length}개 · 상업적 이용 가능 #{counts.fetch("가능", 0)}개 · 불가 #{counts.fetch("불가", 0)}개 · 확인 불가 #{counts.fetch("확인 불가", 0)}개 · 조건 확인 필요 #{counts.fetch("조건 확인 필요", 0)}개"
  readme << ""

  grouped = rows.group_by { |row| category_for(row["평가 축"]) }
  grouped.each do |category, category_rows|
    readme << "### #{category}"
    readme << ""
    readme << "| 벤치마크 | 평가 축 | 설명 | 대표 예시 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |"
    readme << "|---|---|---|---|---|---|---|"
    category_rows.each do |row|
      name = "[#{markdown_escape(row["이름"])}](#{public_url(row["링크"])})"
      license_info = [
        markdown_escape(row["라이선스"]),
        "수정·파생: #{markdown_escape(row["수정·파생"])}",
        "재배포: #{markdown_escape(row["재배포"])}",
        markdown_escape(row["이용 시 유의사항"])
      ].reject(&:empty?).join("<br>")
      example_info = [
        row["대표 과제"].to_s.empty? ? "" : "**#{markdown_escape(row["대표 과제"])}**",
        markdown_escape(row["대표 예시·설명"])
      ].reject(&:empty?).join("<br>")
      readme << "| #{name} | #{markdown_escape(row["평가 축"])} | #{markdown_escape(row["정의"])} | #{example_info} | **#{markdown_escape(row["상업적 이용"])}** | #{license_info} | #{markdown_escape(row["lm-eval 지원"])} |"
    end
    readme << ""
  end
end

readme << "## 데이터 열"
readme << ""
readme << "| 열 | 설명 |"
readme << "|---|---|"
readme << "| `대표 예시·설명` | 실제 또는 대표적인 과제 예시, 번역·요약 설명 |"
readme << "| `예시 표기` | 한국어 예시·요약, 한국어 번역·요약, 영문 예시(한국어 주석) 구분 |"
readme << "| `라이선스` | 데이터 카드 또는 원 출처에 표시된 라이선스와 조사 메모 |"
readme << "| `상업적 이용` | 선언된 라이선스를 기준으로 한 상업적 이용 판단 |"
readme << "| `수정·파생` | 번역, 변형 및 파생 데이터 제작 가능 여부 |"
readme << "| `재배포` | 원본 또는 변형본 재배포 가능 여부 |"
readme << "| `이용 시 유의사항` | 게이트 접근, 원저작권, 실행 환경 및 평가상 주의점 |"
readme << ""
readme << "## 기여 시 확인 사항"
readme << ""
readme << "1. 데이터 카드와 공식 저장소의 라이선스를 우선 확인"
readme << "2. 데이터 라이선스와 코드·평가 하니스 라이선스를 구분"
readme << "3. 번역본·미러·수집물은 원본 라이선스가 자동 승계된다고 가정하지 않기"
readme << "4. 라이선스 재확인 시 문서 상단의 확인 기준일을 갱신"

File.write("README.md", readme.join("\n") + "\n", encoding: "UTF-8")

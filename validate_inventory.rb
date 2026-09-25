#!/usr/bin/env ruby
# frozen_string_literal: true

require "csv"
require "date"
require "uri"

ROOT = File.expand_path(__dir__)
BENCHMARK_HEADERS = [
  "id", "이름", "평가 축", "언어", "정의", "대표 과제", "대표 예시·설명",
  "라이선스", "상업적 이용", "lm-eval 지원", "링크"
].freeze
SERVING_HEADERS = [
  "id", "이름", "분류", "측정 대상", "주요 지표", "부하 방식", "하드웨어 공개",
  "원시 결과", "에어갭", "라이선스", "운영 상태", "최근 확인일", "Benchpress 판단", "설명", "링크"
].freeze
SERVING_ENUMS = {
  "분류" => ["측정 도구", "공개 성능 표준", "공개 성능 보드", "회귀 대시보드", "자원 계측"],
  "에어갭" => ["가능", "조건부", "해당 없음"],
  "운영 상태" => ["활성", "단계적 종료", "유지보수 확인 필요", "초기 공개"],
  "Benchpress 판단" => ["사용 중", "도입 후보", "참고", "보류", "방법론 채택", "관찰", "도입 예정", "대체 수단"]
}.freeze

def read_csv(name)
  CSV.read(File.join(ROOT, name), headers: true, encoding: "bom|utf-8", liberal_parsing: true)
end

def validate_required(table, name, required)
  missing_headers = required - table.headers
  abort "#{name}: missing headers: #{missing_headers.join(', ')}" unless missing_headers.empty?

  table.each_with_index do |row, index|
    missing_values = required.select { |header| row[header].to_s.strip.empty? }
    abort "#{name}: row #{index + 2} missing: #{missing_values.join(', ')}" unless missing_values.empty?
  end
end

def validate_ids(table, name)
  duplicates = table.map { |row| row["id"] }.group_by(&:itself).select { |_id, values| values.length > 1 }.keys
  abort "#{name}: duplicate ids: #{duplicates.join(', ')}" unless duplicates.empty?
end

def validate_https_links(table, name)
  table.each_with_index do |row, index|
    public_link = row["링크"].to_s.split(/\s+\(/, 2).first
    uri = URI.parse(public_link)
    abort "#{name}: row #{index + 2} link must use https" unless uri.is_a?(URI::HTTPS)
  rescue URI::InvalidURIError => error
    abort "#{name}: row #{index + 2}: #{error.message}"
  end
end

def validate_enums(table, name, allowed_values)
  allowed_values.each do |header, allowed|
    invalid = table.each_with_index.map do |row, index|
      "row #{index + 2}: #{row[header]}" unless allowed.include?(row[header])
    end.compact
    abort "#{name}: invalid #{header}: #{invalid.join(', ')}" unless invalid.empty?
  end
end

%w[korean_benchmark_inventory.csv english_benchmark_inventory.csv].each do |name|
  table = read_csv(name)
  validate_required(table, name, BENCHMARK_HEADERS)
  validate_ids(table, name)
  validate_https_links(table, name)
end

english_ids = read_csv("english_benchmark_inventory.csv").map { |row| row["id"] }
english_copy = File.read(File.join(ROOT, "english-copy.js"), encoding: "utf-8")
english_copy_ids = english_copy.scan(/^  (?:"([^"]+)"|([a-z0-9]+)):\s*\{/).map { |quoted, bare| quoted || bare }
missing_copy = english_ids - english_copy_ids
extra_copy = english_copy_ids - english_ids
abort "english-copy.js: missing ids: #{missing_copy.join(', ')}" unless missing_copy.empty?
abort "english-copy.js: unknown ids: #{extra_copy.join(', ')}" unless extra_copy.empty?

serving = read_csv("serving_inventory.csv")
validate_required(serving, "serving_inventory.csv", SERVING_HEADERS)
validate_ids(serving, "serving_inventory.csv")
validate_https_links(serving, "serving_inventory.csv")
validate_enums(serving, "serving_inventory.csv", SERVING_ENUMS)

serving.each_with_index do |row, index|
  Date.iso8601(row["최근 확인일"])
rescue Date::Error => error
  abort "serving_inventory.csv: row #{index + 2}: #{error.message}"
end

%w[index.html korean.html english.html serving.html english-copy.js].each do |name|
  abort "missing page: #{name}" unless File.file?(File.join(ROOT, name))
end

puts "Validated 2 benchmark inventories and #{serving.length} serving records."

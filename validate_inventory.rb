#!/usr/bin/env ruby
# frozen_string_literal: true

require "csv"
require "date"
require "uri"

ROOT = File.expand_path(__dir__)
BENCHMARK_HEADERS = ["id", "이름", "평가 축", "언어", "정의", "라이선스", "상업적 이용", "링크"].freeze
SERVING_HEADERS = [
  "id", "이름", "분류", "측정 대상", "주요 지표", "부하 방식", "하드웨어 공개",
  "원시 결과", "에어갭", "라이선스", "운영 상태", "최근 확인일", "Benchpress 판단", "설명", "링크"
].freeze

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

%w[korean_benchmark_inventory.csv english_benchmark_inventory.csv].each do |name|
  table = read_csv(name)
  validate_required(table, name, BENCHMARK_HEADERS)
  validate_ids(table, name)
end

serving = read_csv("serving_inventory.csv")
validate_required(serving, "serving_inventory.csv", SERVING_HEADERS)
validate_ids(serving, "serving_inventory.csv")

serving.each_with_index do |row, index|
  uri = URI.parse(row["링크"])
  abort "serving_inventory.csv: row #{index + 2} link must use https" unless uri.is_a?(URI::HTTPS)
  Date.iso8601(row["최근 확인일"])
rescue URI::InvalidURIError, Date::Error => error
  abort "serving_inventory.csv: row #{index + 2}: #{error.message}"
end

%w[index.html korean.html english.html serving.html].each do |name|
  abort "missing page: #{name}" unless File.file?(File.join(ROOT, name))
end

puts "Validated 2 benchmark inventories and #{serving.length} serving records."

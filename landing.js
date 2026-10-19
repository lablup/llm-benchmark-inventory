const meta = window.INVENTORY_META ?? {};

const values = {
  "landing-ko-count": meta.korean_count,
  "landing-en-count": meta.english_count,
  "landing-serving-count": meta.serving_count,
  "landing-total-count": (meta.korean_count ?? 0) + (meta.english_count ?? 0) + (meta.serving_count ?? 0),
  "landing-ko-vision-count": meta.korean_vision_count,
  "landing-en-vision-count": meta.english_vision_count,
  "landing-ko-text-count": (meta.korean_count ?? 0) - (meta.korean_vision_count ?? 0),
  "landing-en-text-count": (meta.english_count ?? 0) - (meta.english_vision_count ?? 0),
};

Object.entries(values).forEach(([id, value]) => {
  const element = document.querySelector(`#${id}`);
  if (element) element.textContent = Number.isFinite(value) ? value.toLocaleString("ko-KR") : "—";
});

const updated = document.querySelector("#landing-updated");
if (updated) updated.textContent = meta.serving_checked_at ?? "—";

fetch("./new-papers.json", { cache: "no-cache" }).then(response => {
  if (!response.ok) throw new Error("Could not load paper summary");
  return response.json();
}).then(data => {
  const summary = document.querySelector("#landing-papers-status");
  if (!summary) return;
  const pending = data.papers.filter(paper => paper.analysis_status === "accepted").length;
  const checked = data.last_checked_at ? new Date(data.last_checked_at) : null;
  const date = checked ? checked.toLocaleDateString("ko-KR", { timeZone: "Asia/Seoul" }) : "첫 수집 대기";
  const stale = checked && Date.now() - checked.getTime() >= 3 * 86400000 ? " · 수집 지연, 자동 갱신 상태 확인 필요" : "";
  summary.textContent = `수집한 논문 ${data.papers.length}건 · 자동 반영 ${pending}건 · ${date}${stale}${data.discovery_error ? " · arXiv 신규 수집 지연" : ""}${data.research?.status === "not_configured" ? " · 자동 조사 API 연결 대기" : ""}`;
}).catch(() => {
  const summary = document.querySelector("#landing-papers-status");
  if (summary) summary.textContent = "수집 기록을 불러오지 못했습니다. 새 논문 페이지에서 확인해 주세요.";
});

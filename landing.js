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

fetch("./updates.json", { cache: "no-cache" }).then(response => {
  if (!response.ok) throw new Error("Could not load updates");
  return response.json();
}).then(data => {
  const summary = document.querySelector("#landing-papers-status");
  if (!summary || !data.updates?.length) return;
  const latest = data.updates[0];
  const date = latest.applied_at ? new Date(latest.applied_at).toLocaleDateString("ko-KR", { timeZone: "Asia/Seoul" }) + " · " : "";
  summary.textContent = date + latest.changes.map(change => `${change.name} ${change.action === "added" ? "추가" : "수정"}: ${change.summary}`).join(" ");
}).catch(() => {
  const summary = document.querySelector("#landing-papers-status");
  if (summary) summary.textContent = "벤치마크 표에 반영된 추가·수정 내역은 업데이트 페이지에서 확인할 수 있습니다.";
});

fetch("./research-status.json", { cache: "no-cache" }).then(response => {
  if (!response.ok) throw new Error("Could not load research status");
  return response.json();
}).then(data => {
  const target = document.querySelector("#landing-research-status");
  const day = data.days?.[data.days.length - 1];
  if (!target || !day) return;
  const c = day.counts;
  target.textContent = `자동 조사 ${day.day}: 본문 시도 ${day.attempted}건 · PDF 실패 ${c.pdf_failed}건 · 보류 ${c.held}건 · 제외 ${c.excluded}건 · 표 반영 ${c.published}건 · 대기 ${data.totals.queued}건`;
}).catch(() => {});

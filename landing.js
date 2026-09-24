const meta = window.INVENTORY_META ?? {};

const values = {
  "landing-ko-count": meta.korean_count,
  "landing-en-count": meta.english_count,
  "landing-serving-count": meta.serving_count,
  "landing-total-count": (meta.korean_count ?? 0) + (meta.english_count ?? 0) + (meta.serving_count ?? 0),
};

Object.entries(values).forEach(([id, value]) => {
  const element = document.querySelector(`#${id}`);
  if (element) element.textContent = Number.isFinite(value) ? value.toLocaleString("ko-KR") : "—";
});

const updated = document.querySelector("#landing-updated");
if (updated) updated.textContent = meta.serving_checked_at ?? "—";

const state = {
  rows: [],
  language: "all",
  query: "",
  commercial: "",
  lmeval: "",
};

const elements = {
  grid: document.querySelector("#benchmark-grid"),
  count: document.querySelector("#result-count"),
  empty: document.querySelector("#empty-state"),
  search: document.querySelector("#search-input"),
  commercial: document.querySelector("#commercial-filter"),
  lmeval: document.querySelector("#lmeval-filter"),
  tabs: [...document.querySelectorAll("[data-language]")],
  reset: document.querySelector("#reset-filters"),
};

function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    const next = text[index + 1];

    if (character === '"' && quoted && next === '"') {
      field += '"';
      index += 1;
    } else if (character === '"') {
      quoted = !quoted;
    } else if (character === "," && !quoted) {
      row.push(field);
      field = "";
    } else if ((character === "\n" || character === "\r") && !quoted) {
      if (character === "\r" && next === "\n") index += 1;
      row.push(field);
      if (row.some((value) => value.length)) rows.push(row);
      row = [];
      field = "";
    } else {
      field += character;
    }
  }

  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }

  const headers = rows.shift().map((header) => header.replace(/^\uFEFF/, ""));
  return rows.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
}

function escapeHTML(value) {
  return value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[character]);
}

function statusClass(status) {
  if (status === "가능") return "good";
  if (status === "불가") return "bad";
  return "caution";
}

function isLmEvalSupported(value) {
  return value !== "없음" && value.trim() !== "";
}

function renderExample(row) {
  const example = (row["대표 예시·설명"] ?? "").trim();
  if (!example) return "";
  const task = (row["대표 과제"] ?? "").trim();
  return `
    <div class="example">
      <p class="example-title">대표 예시${task ? ` · ${escapeHTML(task)}` : ""}</p>
      <p class="example-body">${escapeHTML(example)}</p>
    </div>
  `;
}

function renderRow(row) {
  const language = row["언어"] === "ko" ? "KOREAN" : "ENGLISH";
  const lmEval = isLmEvalSupported(row["lm-eval 지원"]) ? row["lm-eval 지원"] : "미지원";
  return `
    <article class="list-row">
      <div class="benchmark-name">
        <span class="language">${language}</span>
        <h3><a href="${escapeHTML(row["링크"])}" target="_blank" rel="noopener noreferrer">${escapeHTML(row["이름"])} <span aria-hidden="true">↗</span></a></h3>
        <p>${escapeHTML(row["정의"])}</p>
        ${renderExample(row)}
      </div>
      <p class="list-axis">${escapeHTML(row["평가 축"])}</p>
      <div class="license-cell">
        <span class="status ${statusClass(row["상업적 이용"])}">${escapeHTML(row["상업적 이용"])}</span>
        <span>${escapeHTML(row["라이선스"])}</span>
      </div>
      <p class="lmeval">${escapeHTML(lmEval)}</p>
    </article>
  `;
}

function renderGroup(category, rows) {
  return `
    <section class="benchmark-group">
      <div class="group-title">
        <h3>${escapeHTML(category)}</h3>
        <span>${rows.length}</span>
      </div>
      <div class="list-head" aria-hidden="true">
        <span>벤치마크 / 설명</span>
        <span>평가 축</span>
        <span>상업 이용 / 라이선스</span>
        <span>lm-eval</span>
      </div>
      ${rows.map(renderRow).join("")}
    </section>
  `;
}

function filteredRows() {
  const query = state.query.toLocaleLowerCase("ko");
  return state.rows.filter((row) => {
    const searchable = [row["이름"], row["평가 축"], row["정의"], row["대표 과제"], row["대표 예시·설명"], row["라이선스"]].join(" ").toLocaleLowerCase("ko");
    const languageMatches = state.language === "all" || row["언어"] === state.language;
    const queryMatches = !query || searchable.includes(query);
    const commercialMatches = !state.commercial || row["상업적 이용"] === state.commercial;
    const supported = isLmEvalSupported(row["lm-eval 지원"]);
    const lmevalMatches = !state.lmeval || (state.lmeval === "supported" ? supported : !supported);
    return languageMatches && queryMatches && commercialMatches && lmevalMatches;
  });
}

function render() {
  const rows = filteredRows();
  const groups = rows.reduce((result, row) => {
    const category = row["분류"] || "기타";
    if (!result.has(category)) result.set(category, []);
    result.get(category).push(row);
    return result;
  }, new Map());
  elements.grid.innerHTML = [...groups].map(([category, items]) => renderGroup(category, items)).join("");
  elements.count.textContent = rows.length.toLocaleString("ko-KR");
  elements.empty.hidden = rows.length > 0;
}

function resetFilters() {
  state.language = "all";
  state.query = "";
  state.commercial = "";
  state.lmeval = "";
  elements.search.value = "";
  elements.commercial.value = "";
  elements.lmeval.value = "";
  elements.tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.language === "all"));
  render();
}

async function loadInventory() {
  try {
    if (Array.isArray(window.BENCHMARK_INVENTORY)) {
      state.rows = window.BENCHMARK_INVENTORY;
    } else {
      const sources = ["korean_benchmark_inventory.csv", "english_benchmark_inventory.csv"];
      const responses = await Promise.all(sources.map((source) => fetch(source)));
      if (responses.some((response) => !response.ok)) throw new Error("CSV request failed");
      state.rows = (await Promise.all(responses.map((response) => response.text()))).flatMap(parseCSV);
    }

    state.query = elements.search.value.trim();
    state.commercial = elements.commercial.value;
    state.lmeval = elements.lmeval.value;
    document.querySelector("#stat-total").textContent = state.rows.length;
    document.querySelector("#stat-commercial").textContent = state.rows.filter((row) => row["상업적 이용"] === "가능").length;
    document.querySelector("#stat-lmeval").textContent = state.rows.filter((row) => isLmEvalSupported(row["lm-eval 지원"])).length;
    render();
  } catch (error) {
    elements.grid.innerHTML = '<p class="empty-state">데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.</p>';
    console.error(error);
  }
}

elements.tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    state.language = tab.dataset.language;
    elements.tabs.forEach((item) => item.classList.toggle("active", item === tab));
    render();
  });
});
elements.search.addEventListener("input", (event) => { state.query = event.target.value.trim(); render(); });
elements.commercial.addEventListener("change", (event) => { state.commercial = event.target.value; render(); });
elements.lmeval.addEventListener("change", (event) => { state.lmeval = event.target.value; render(); });
elements.reset.addEventListener("click", resetFilters);
elements.empty.querySelector("button").addEventListener("click", resetFilters);

loadInventory();

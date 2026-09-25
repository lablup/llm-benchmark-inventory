const servingState = {
  rows: [],
  query: "",
  category: "",
  airgap: "",
};

const servingElements = {
  grid: document.querySelector("#serving-grid"),
  count: document.querySelector("#result-count"),
  empty: document.querySelector("#empty-state"),
  search: document.querySelector("#search-input"),
  category: document.querySelector("#category-filter"),
  airgap: document.querySelector("#airgap-filter"),
  reset: document.querySelector("#reset-filters"),
};

function parseServingCSV(text) {
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

function escapeServingHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[character]);
}

function decisionClass(value) {
  if (["사용 중", "도입 예정", "방법론 채택"].includes(value)) return "good";
  if (["보류"].includes(value)) return "bad";
  return "caution";
}

function renderServingRow(row) {
  return `
    <article class="serving-row">
      <div class="benchmark-name">
        <span class="language">${escapeServingHTML(row["분류"])}</span>
        <h3><a href="${escapeServingHTML(row["링크"])}" target="_blank" rel="noopener noreferrer">${escapeServingHTML(row["이름"])} <span aria-hidden="true">↗</span></a></h3>
        <p>${escapeServingHTML(row["설명"])}</p>
      </div>
      <div class="serving-detail">
        <strong>${escapeServingHTML(row["측정 대상"])}</strong>
        <span>${escapeServingHTML(row["부하 방식"])}</span>
      </div>
      <p class="serving-metrics">${escapeServingHTML(row["주요 지표"])}</p>
      <div class="license-cell">
        <span class="status ${decisionClass(row["Benchpress 판단"])}">${escapeServingHTML(row["Benchpress 판단"])}</span>
        <span>에어갭 ${escapeServingHTML(row["에어갭"])} · ${escapeServingHTML(row["운영 상태"])}</span>
      </div>
    </article>
  `;
}

function filteredServingRows() {
  const query = servingState.query.toLocaleLowerCase("ko");
  return servingState.rows.filter((row) => {
    const searchable = Object.values(row).join(" ").toLocaleLowerCase("ko");
    return (!query || searchable.includes(query))
      && (!servingState.category || row["분류"] === servingState.category)
      && (!servingState.airgap || row["에어갭"] === servingState.airgap);
  });
}

function renderServing() {
  const rows = filteredServingRows();
  const groups = rows.reduce((result, row) => {
    const category = row["분류"] || "기타";
    if (!result.has(category)) result.set(category, []);
    result.get(category).push(row);
    return result;
  }, new Map());
  servingElements.grid.innerHTML = [...groups].map(([category, items]) => `
    <section class="benchmark-group">
      <div class="group-title"><h3>${escapeServingHTML(category)}</h3><span>${items.length}</span></div>
      <div class="serving-head" aria-hidden="true">
        <span>도구·보드 / 설명</span><span>대상 / 부하</span><span>주요 지표</span><span>Benchpress 판단</span>
      </div>
      ${items.map(renderServingRow).join("")}
    </section>
  `).join("");
  servingElements.count.textContent = rows.length.toLocaleString("ko-KR");
  servingElements.empty.hidden = rows.length > 0;
}

function resetServingFilters() {
  servingState.query = "";
  servingState.category = "";
  servingState.airgap = "";
  servingElements.search.value = "";
  servingElements.category.value = "";
  servingElements.airgap.value = "";
  renderServing();
}

async function loadServingInventory() {
  if (Array.isArray(window.SERVING_INVENTORY)) {
    servingState.rows = window.SERVING_INVENTORY;
  } else {
    const response = await fetch("serving_inventory.csv");
    if (!response.ok) throw new Error("Serving inventory request failed");
    servingState.rows = parseServingCSV(await response.text());
  }

  document.querySelector("#stat-serving-total").textContent = servingState.rows.length;
  document.querySelector("#stat-serving-active").textContent = servingState.rows.filter((row) => row["운영 상태"] === "활성").length;
  document.querySelector("#stat-serving-airgap").textContent = servingState.rows.filter((row) => row["에어갭"] === "가능").length;
  renderServing();
}

servingElements.search.addEventListener("input", (event) => { servingState.query = event.target.value.trim(); renderServing(); });
servingElements.category.addEventListener("change", (event) => { servingState.category = event.target.value; renderServing(); });
servingElements.airgap.addEventListener("change", (event) => { servingState.airgap = event.target.value; renderServing(); });
servingElements.reset.addEventListener("click", resetServingFilters);
servingElements.empty.querySelector("button").addEventListener("click", resetServingFilters);

const servingSwitcher = document.querySelector(".track-switcher");
if (servingSwitcher) {
  servingSwitcher.innerHTML = '<a href="./korean.html">텍스트</a><a href="./korean.html?modality=vision">이미지</a><a aria-current="page" href="./serving.html">서빙</a>';
}

loadServingInventory().catch((error) => {
  servingElements.grid.innerHTML = '<p class="empty-state">데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.</p>';
  console.error(error);
});

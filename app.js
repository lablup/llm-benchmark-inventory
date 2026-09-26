const state = {
  rows: [],
  language: document.body.dataset.language || "all",
  uiLanguage: document.body.dataset.uiLanguage || document.documentElement.lang || "ko",
  modality: new URLSearchParams(window.location.search).get("modality") === "vision" ? "vision" : "text",
  query: "",
  commercial: "",
  lmeval: "",
};

const VISION_GROUPS = new Map([
  ["ko:kmmmu", "일반"],
  ["ko:haerae-vision", "일반"],
  ["ko:koffvqa", "일반"],
  ["ko:kreta", "일반"],
  ["ko:k-dtcbench", "일반"],
  ["ko:k-mmbench", "일반"],
  ["ko:ksafe-mm", "위험 탐지"],
  ["ko:kormedmcqa-v", "의료"],
  ["en:hle", "이미지"],
  ["en:arc-agi-2", "이미지"],
  ["en:gaia", "이미지"],
  ["en:osworld", "이미지"],
]);
const VISION_GROUP_ORDER = ["일반", "위험 탐지", "의료", "이미지"];

document.body.dataset.modality = state.modality;

const elements = {
  grid: document.querySelector("#benchmark-grid"),
  count: document.querySelector("#result-count"),
  empty: document.querySelector("#empty-state"),
  search: document.querySelector("#search-input"),
  commercial: document.querySelector("#commercial-filter"),
  lmeval: document.querySelector("#lmeval-filter"),
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
  return !value.trim().startsWith("없음") && value.trim() !== "";
}

const ENGLISH_CATEGORIES = {
  "이해·언어": "Knowledge and language",
  "추론·수학": "Reasoning and mathematics",
  "지시이행": "Instruction following",
  "코딩": "Coding",
  "에이전트·도구 사용": "Agents and tool use",
  "안전·사실성": "Safety and factuality",
  "검색·RAG·장문": "Retrieval and long context",
  "생성·평가": "Generation and evaluation",
  "기타": "Other evaluations",
  "이미지": "Vision benchmarks",
};

const ENGLISH_LICENSES = {
  "MIT 태그(README 재배포 제한 문구와 충돌. 이용 전 확인)": "MIT tag; repository terms conflict and require review",
  "미표기": "Not specified",
  "미표기(원본 MATH=MIT)": "Not specified; the original MATH dataset uses MIT",
  "미표기(HF 미러에 라이선스 필드 부재)": "Not specified in the Hugging Face mirror",
  "비공개 홀드아웃": "Private holdout",
  "공식 사이트 확인 필요(공개 저장소 미확인)": "Review the official site; no public repository was found",
  "카드 'cc' 표기(모호. 확인 필요)": "Dataset card says 'cc'; clarification is required",
  "미표기(수집물. 원 저장소 라이선스 상속)": "Not specified; source repository licenses may apply",
  "미표기 + HF 게이트": "Not specified; Hugging Face access approval is required",
  "CC-BY-4.0(미러 카드)": "CC-BY-4.0, as stated on the mirror card",
  "Apache-2.0(FastChat 저장소)": "Apache-2.0 for the FastChat repository",
};

function localizeEnglishRow(row) {
  if (state.uiLanguage !== "en") return row;
  const copy = window.ENGLISH_INVENTORY_COPY?.[row.id];
  if (!copy) return row;
  return {
    ...row,
    "평가 축": copy.axis,
    "정의": copy.definition,
    "대표 과제": copy.task,
    "대표 예시·설명": copy.example,
  };
}

function commercialLabel(status) {
  if (state.uiLanguage !== "en") return status;
  return ({
    "가능": "Allowed",
    "불가": "Not allowed",
    "조건 확인 필요": "Review required",
    "확인 불가": "Unknown",
  })[status] || status;
}

function licenseLabel(license) {
  if (state.uiLanguage !== "en") return license;
  return ENGLISH_LICENSES[license] || license;
}

function lmEvalLabel(value) {
  if (state.uiLanguage !== "en") return isLmEvalSupported(value) ? value : "미지원";
  if (!isLmEvalSupported(value)) return "Not supported";
  return value.replace(/^내장/, "Built in").replace("500 부분집합은 별도", "the 500-question subset is separate");
}

function matchesModality(row) {
  const isVision = VISION_GROUPS.has(`${row["트랙"]}:${row.id}`);
  return state.modality === "vision" ? isVision : !isVision;
}

function updatePageNavigation() {
  const switcher = document.querySelector(".track-switcher");
  if (!switcher) return;
  const koreanUI = state.uiLanguage !== "en";
  const koreanData = state.language === "ko";
  const pageName = koreanData ? "korean" : "english";
  const visionQuery = state.modality === "vision" ? "?modality=vision" : "";
  switcher.classList.add("track-switcher--tiered");
  if (koreanUI) {
    switcher.innerHTML = `
      <div class="switch-group" aria-label="평가 대상">
        <a ${state.modality === "text" ? 'aria-current="page"' : ""} href="./${pageName}.html">텍스트</a>
        <a ${state.modality === "vision" ? 'aria-current="page"' : ""} href="./${pageName}.html?modality=vision">이미지</a>
        <a href="./serving.html">서빙</a>
      </div>
      <div class="switch-group" aria-label="평가 언어">
        <a ${koreanData ? 'aria-current="page"' : ""} href="./korean.html${visionQuery}">한국어</a>
        <a ${koreanData ? "" : 'aria-current="page"'} href="./english.html${visionQuery}">영어</a>
      </div>
    `;
    return;
  }
  switcher.innerHTML = `
    <div class="switch-group" aria-label="Evaluation input">
      <a ${state.modality === "text" ? 'aria-current="page"' : ""} href="./${pageName}.html">Text</a>
      <a ${state.modality === "vision" ? 'aria-current="page"' : ""} href="./${pageName}.html?modality=vision">Vision</a>
      <a href="./serving.html">Serving</a>
    </div>
    <div class="switch-group" aria-label="Language">
      <a ${koreanData ? 'aria-current="page"' : ""} href="./korean.html${visionQuery}">Korean</a>
      <a ${koreanData ? "" : 'aria-current="page"'} href="./english.html${visionQuery}">English</a>
    </div>
  `;
}

function updatePageContext() {
  if (state.modality !== "vision") return;

  const koreanUI = state.uiLanguage !== "en";
  const koreanData = state.language === "ko";
  const languageName = koreanData ? "한국어" : "영어";
  const heroTitle = document.querySelector(".hero-content h1");
  const heroCopy = document.querySelector(".hero-copy");
  const summaryTitle = document.querySelector("#summary-title");
  const inventoryTitle = document.querySelector("#inventory-title");
  const firstStat = document.querySelector(".stats dd");
  const notes = document.querySelector(".reading-notes");

  document.title = koreanUI ? `${languageName} 이미지 벤치마크 · LLM 벤치마크 인벤토리` : "English Vision Benchmarks · LLM Benchmark Inventory";
  if (heroTitle) heroTitle.innerHTML = koreanUI ? `${languageName} 이미지<br><span>벤치마크</span>` : "English vision<br><span>benchmarks</span>";
  if (heroCopy) heroCopy.textContent = koreanUI
    ? `이미지, 문서와 화면을 입력으로 사용하는 ${languageName} 평가 자료를 확인합니다.`
    : "Review English-language evaluations that use images, documents, or computer screens as input.";
  if (summaryTitle) summaryTitle.textContent = koreanUI ? `${languageName} 이미지 평가` : "English vision evaluations";
  if (inventoryTitle) inventoryTitle.textContent = koreanUI ? `${languageName} 이미지 벤치마크` : "English vision benchmarks";
  if (firstStat) firstStat.textContent = koreanUI ? "이미지 항목" : "Vision benchmarks";
  if (notes) notes.innerHTML = koreanUI && koreanData
    ? "<li><strong>일반:</strong> 장면, 문서, 도표와 한국 문화에 관한 이미지 이해를 평가합니다.</li><li><strong>위험 탐지:</strong> 유해 이미지를 판단하고 안전하게 답하는지, 편향되거나 필요 이상으로 거부하지 않는지 확인합니다.</li><li><strong>의료:</strong> 의료 영상을 해석하고 여러 영상을 함께 살펴 한국어 임상 문항에 답하는 능력을 평가합니다.</li>"
    : koreanUI
      ? "<li><strong>입력 형식:</strong> 이미지, 문서, 표 또는 화면 가운데 평가에 사용하는 입력을 확인합니다.</li><li><strong>실행 환경:</strong> 이미지 해상도와 모델 입력 형식을 결과와 함께 기록해야 합니다.</li><li><strong>이용 조건:</strong> 이미지와 원문 문항의 권리를 데이터셋 라이선스와 별도로 확인해야 합니다.</li>"
    : "<li><strong>Input format:</strong> Check whether each evaluation uses images, documents, charts, or computer screens.</li><li><strong>Runtime:</strong> Record the image resolution and model input format with every result.</li><li><strong>Licensing:</strong> Review the rights for images and original questions separately from the dataset license.</li>";
}

function renderExample(row) {
  const example = (row["대표 예시·설명"] ?? "").trim();
  if (!example) return "";
  const task = (row["대표 과제"] ?? "").trim();
  return `
    <div class="example">
      <p class="example-title">${state.uiLanguage === "en" ? "Example" : "대표 예시"}${task ? ` · ${escapeHTML(task)}` : ""}</p>
      <p class="example-body">${escapeHTML(example)}</p>
    </div>
  `;
}

function renderRow(row) {
  const language = state.uiLanguage === "en" ? (row["트랙"] === "ko" ? "KOREAN" : "ENGLISH") : (row["트랙"] === "ko" ? "한국어" : "영어");
  const lmEval = lmEvalLabel(row["lm-eval 지원"]);
  return `
    <article class="list-row">
      <div class="benchmark-name">
        <span class="language">${language}</span>
        <h3><a href="${escapeHTML(row["링크"])}" target="_blank" rel="noopener noreferrer">${escapeHTML(row["이름"])} <span aria-hidden="true">↗</span></a></h3>
        <p>${escapeHTML(row["정의"])}</p>
      </div>
      <p class="list-axis">${escapeHTML(row["평가 축"])}</p>
      <div class="license-cell">
        <span class="status ${statusClass(row["상업적 이용"])}">${escapeHTML(commercialLabel(row["상업적 이용"]))}</span>
        <span>${escapeHTML(licenseLabel(row["라이선스"]))}</span>
      </div>
      <p class="lmeval">${escapeHTML(lmEval)}</p>
      ${renderExample(row)}
    </article>
  `;
}

function renderGroup(category, rows) {
  const english = state.uiLanguage === "en";
  return `
    <section class="benchmark-group">
      <div class="group-title">
        <h3>${escapeHTML(category)}</h3>
        <span>${rows.length}</span>
      </div>
      <div class="list-head" aria-hidden="true">
        <span>${english ? "Benchmark / description" : "벤치마크 / 설명"}</span>
        <span>${english ? "Evaluation category" : "평가 축"}</span>
        <span>${english ? "Commercial use / license" : "상업 이용 / 라이선스"}</span>
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
    const languageMatches = state.language === "all" || row["트랙"] === state.language;
    const modalityMatches = matchesModality(row);
    const queryMatches = !query || searchable.includes(query);
    const commercialMatches = !state.commercial || row["상업적 이용"] === state.commercial;
    const supported = isLmEvalSupported(row["lm-eval 지원"]);
    const lmevalMatches = !state.lmeval || (state.lmeval === "supported" ? supported : !supported);
    return languageMatches && modalityMatches && queryMatches && commercialMatches && lmevalMatches;
  });
}

function render() {
  const rows = filteredRows();
  const groups = rows.reduce((result, row) => {
    const sourceCategory = state.modality === "vision"
      ? (VISION_GROUPS.get(`${row["트랙"]}:${row.id}`) || "이미지")
      : (row["분류"] || "기타");
    const category = state.uiLanguage === "en" ? (ENGLISH_CATEGORIES[sourceCategory] || sourceCategory) : sourceCategory;
    if (!result.has(category)) result.set(category, []);
    result.get(category).push(row);
    return result;
  }, new Map());
  const sortedGroups = [...groups].sort(([left], [right]) => {
    if (state.modality !== "vision") return 0;
    const leftIndex = VISION_GROUP_ORDER.indexOf(left);
    const rightIndex = VISION_GROUP_ORDER.indexOf(right);
    return (leftIndex < 0 ? VISION_GROUP_ORDER.length : leftIndex)
      - (rightIndex < 0 ? VISION_GROUP_ORDER.length : rightIndex);
  });
  elements.grid.innerHTML = sortedGroups.map(([category, items]) => renderGroup(category, items)).join("");
  elements.count.textContent = rows.length.toLocaleString(state.uiLanguage === "en" ? "en-US" : "ko-KR");
  elements.empty.hidden = rows.length > 0;
}

function resetFilters() {
  state.language = document.body.dataset.language || "all";
  state.query = "";
  state.commercial = "";
  state.lmeval = "";
  elements.search.value = "";
  elements.commercial.value = "";
  elements.lmeval.value = "";
  render();
}

async function loadInventory() {
  try {
    if (Array.isArray(window.BENCHMARK_INVENTORY)) {
      state.rows = window.BENCHMARK_INVENTORY.map(localizeEnglishRow);
    } else {
      const sources = ["korean_benchmark_inventory.csv", "english_benchmark_inventory.csv"];
      const responses = await Promise.all(sources.map((source) => fetch(source)));
      if (responses.some((response) => !response.ok)) throw new Error("CSV request failed");
      const parsed = (await Promise.all(responses.map((response) => response.text()))).map(parseCSV);
      state.rows = parsed.flatMap((rows, index) => rows.map((row) => localizeEnglishRow({ ...row, "트랙": index === 0 ? "ko" : "en" })));
    }

    const trackRows = state.rows.filter((row) => (state.language === "all" || row["트랙"] === state.language) && matchesModality(row));
    state.query = elements.search.value.trim();
    state.commercial = elements.commercial.value;
    state.lmeval = elements.lmeval.value;
    document.querySelector("#stat-total").textContent = trackRows.length;
    document.querySelector("#stat-commercial").textContent = trackRows.filter((row) => row["상업적 이용"] === "가능").length;
    document.querySelector("#stat-lmeval").textContent = trackRows.filter((row) => isLmEvalSupported(row["lm-eval 지원"])).length;
    render();
  } catch (error) {
    elements.grid.innerHTML = `<p class="empty-state">${state.uiLanguage === "en" ? "The benchmark data could not be loaded. Please try again." : "데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."}</p>`;
    console.error(error);
  }
}

elements.search.addEventListener("input", (event) => { state.query = event.target.value.trim(); render(); });
elements.commercial.addEventListener("change", (event) => { state.commercial = event.target.value; render(); });
elements.lmeval.addEventListener("change", (event) => { state.lmeval = event.target.value; render(); });
elements.reset.addEventListener("click", resetFilters);
elements.empty.querySelector("button").addEventListener("click", resetFilters);

updatePageNavigation();
updatePageContext();
loadInventory();

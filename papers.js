(() => {
  const list = document.querySelector("#paper-list");
  const query = document.querySelector("#paper-query");
  const status = document.querySelector("#paper-status");
  const count = document.querySelector("#papers-count");
  const more = document.querySelector("#papers-more");
  let papers = [];
  let limit = 30;
  const chosen = new URLSearchParams(location.search).get("status");
  if (["accepted", "queued", "needs_evidence"].includes(chosen)) status.value = chosen;

  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  const states = { queued: "자동 조사 대기", proposed: "반영 전 확인 중", accepted: "표 반영 완료", held: "보류", rejected: "제외", exclude: "조사 결과 제외", needs_evidence: "근거·판단 불충분으로 미반영" };

  function card(paper) {
    const article = element("article", "", "paper-card");
    article.id = `arxiv-${paper.arxiv_id}`;
    article.append(element("span", states[paper.analysis_status] || states.queued, `paper-status ${paper.analysis_status || "queued"}`));
    const heading = element("h2");
    const link = element("a", paper.title);
    link.href = `https://arxiv.org/abs/${encodeURIComponent(paper.arxiv_id)}`;
    heading.append(link);
    article.append(heading);
    article.append(element("p", `첫 제출 ${paper.published.slice(0, 10)} · ${paper.categories.join(" · ")} · arXiv:${paper.arxiv_id}`, "papers-meta"));
    const authors = paper.authors.slice(0, 6).join(", ") + (paper.authors.length > 6 ? ` 외 ${paper.authors.length - 6}명` : "");
    article.append(element("p", authors, "papers-meta"));
    const details = element("details");
    details.append(element("summary", "초록 원문 보기"), element("p", paper.summary));
    article.append(details);
    if (/^https:\/\/github\.com\/lablup\/llm-benchmark-inventory\/issues\/\d+$/.test(paper.review_issue_url || "")) {
      const review = element("a", "변경안과 처리 결과 보기 →");
      review.href = paper.review_issue_url;
      article.append(review);
    } else {
      article.append(element("p", paper.analysis_reason || "자동 조사 대상입니다. 직접 읽고 검토할 필요는 없습니다.", "papers-meta"));
    }
    return article;
  }

  function render() {
    const text = query.value.trim().toLocaleLowerCase();
    const filtered = papers.filter(p => (status.value === "all" || (status.value === "reviewed" ? p.review_status === "reviewed" : (p.analysis_status || "queued") === status.value))
      && `${p.title} ${p.summary} ${p.authors.join(" ")} ${p.arxiv_id}`.toLocaleLowerCase().includes(text));
    const pending = papers.filter(p => p.analysis_status === "accepted").length;
    count.textContent = `수집 ${papers.length}건 · 자동 반영 ${pending}건 · 현재 ${filtered.length}건`;
    list.replaceChildren(...filtered.slice(0, limit).map(card));
    if (!filtered.length) list.append(element("p", papers.length ? "조건에 맞는 논문이 없습니다." : "아직 수집된 후보가 없습니다."));
    more.hidden = filtered.length <= limit;
  }

  query.addEventListener("input", () => { limit = 30; render(); });
  status.addEventListener("change", () => { limit = 30; render(); });
  more.addEventListener("click", () => { limit += 30; render(); });
  fetch("./new-papers.json", { cache: "no-cache" }).then(response => {
    if (!response.ok) throw new Error("Could not load papers");
    return response.json();
  }).then(data => {
    if (data.schema_version !== 1 || !Array.isArray(data.papers)) throw new Error("Invalid paper data");
    papers = data.papers;
    const research = document.querySelector("#research-status");
    if (data.research?.status === "not_configured") research.textContent = data.research.message;
    else if (data.research?.last_run_at) research.textContent = `최근 자동 조사 ${new Date(data.research.last_run_at).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" })} (한국 시간)`;
    const checked = data.last_checked_at ? new Date(data.last_checked_at) : null;
    document.querySelector("#papers-updated").textContent = checked
      ? `마지막 수집 ${checked.toLocaleString("ko-KR", { timeZone: "Asia/Seoul" })} (한국 시간) · 매일 오전 11시 30분경 갱신`
      : "첫 자동 수집을 기다리고 있습니다.";
    document.querySelector("#papers-stale").hidden = !checked || Date.now() - checked.getTime() < 3 * 86400000;
    render();
  }).catch(() => {
    document.querySelector("#papers-updated").textContent = "수집 기록을 불러오지 못했습니다.";
    count.textContent = "논문 목록을 불러오지 못했습니다. 잠시 후 새로고침하거나 GitHub 검토 이슈를 확인해 주세요.";
  });
})();

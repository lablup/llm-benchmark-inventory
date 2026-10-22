(() => {
  const list = document.querySelector("#paper-list");
  const query = document.querySelector("#paper-query");
  const count = document.querySelector("#papers-count");
  const more = document.querySelector("#papers-more");
  let updates = [];
  let limit = 30;

  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function date(value) {
    return value ? new Date(value).toLocaleDateString("ko-KR", { timeZone: "Asia/Seoul" }) : "";
  }

  function card(update) {
    const article = element("article", "", "paper-card");
    article.id = `arxiv-${update.arxiv_id}`;
    if (update.applied_at) article.append(element("p", date(update.applied_at), "papers-meta"));
    for (const change of update.changes) {
      const heading = element("h2");
      const link = element("a", `${change.name} ${change.action === "added" ? "추가" : "수정"}`);
      if (/^\.\/(korean|english)\.html(?:\?modality=vision)?#inventory$/.test(change.inventory_url)) {
        link.href = change.inventory_url;
      }
      heading.append(link);
      article.append(heading, element("p", change.summary, "papers-meta"));
    }
    const source = element("a", `근거 논문: ${update.title} ↗`);
    source.href = `https://arxiv.org/abs/${encodeURIComponent(update.arxiv_id)}`;
    const links = element("p", "", "papers-meta");
    links.append(source);
    if (/^https:\/\/github\.com\/lablup\/llm-benchmark-inventory\/issues\/\d+$/.test(update.issue_url || "")) {
      const details = element("a", "변경 상세 ↗");
      details.href = update.issue_url;
      links.append(document.createTextNode(" · "), details);
    }
    article.append(links);
    return article;
  }

  function render() {
    const text = query.value.trim().toLocaleLowerCase();
    const filtered = updates.filter(u => `${u.title} ${u.arxiv_id} ${u.changes.map(c => `${c.name} ${c.summary}`).join(" ")}`.toLocaleLowerCase().includes(text));
    count.textContent = updates.length ? `${filtered.length}건` : "";
    list.hidden = !updates.length;
    list.replaceChildren(...filtered.slice(0, limit).map(card));
    if (updates.length && !filtered.length) list.append(element("p", "검색 결과가 없습니다."));
    more.hidden = filtered.length <= limit;
    document.querySelector(".papers-filters").hidden = !updates.length;
  }

  query.addEventListener("input", () => { limit = 30; render(); });
  more.addEventListener("click", () => { limit += 30; render(); });
  fetch("./updates.json", { cache: "no-cache" }).then(response => {
    if (!response.ok) throw new Error("Could not load updates");
    return response.json();
  }).then(data => {
    if (data.schema_version !== 1 || !Array.isArray(data.updates)) throw new Error("Invalid update data");
    updates = data.updates;
    const updated = document.querySelector("#papers-updated");
    updated.hidden = !data.last_updated_at;
    updated.textContent = data.last_updated_at ? `최근 반영 ${date(data.last_updated_at)}` : "";
    render();
  }).catch(() => {
    count.textContent = "업데이트 내역을 불러오지 못했습니다. 잠시 후 새로고침해 주세요.";
  });

  // 조사 현황: every collected paper with its stage, reason and retry date.
  const researchList = document.querySelector("#research-list");
  const researchQuery = document.querySelector("#research-query");
  const researchStage = document.querySelector("#research-stage");
  const researchCount = document.querySelector("#research-count");
  const researchMore = document.querySelector("#research-more");
  const researchDays = document.querySelector("#research-days");
  let research = null;
  let researchLimit = 50;

  function researchCard(record) {
    const article = element("article", "", "paper-card research-card");
    const badge = element("span", record.stage_label, `paper-status stage-${record.stage}`);
    const meta = element("p", "", "papers-meta");
    meta.append(badge);
    if (record.updated_at) meta.append(document.createTextNode(` · ${date(record.updated_at)}`));
    if (record.retry_after) meta.append(document.createTextNode(` · ${record.retry_after}부터 재시도`));
    article.append(meta);
    const heading = element("h2");
    const link = element("a", record.title || record.arxiv_id);
    link.href = `https://arxiv.org/abs/${encodeURIComponent(record.arxiv_id)}`;
    heading.append(link);
    article.append(heading);
    if (record.reason) article.append(element("p", record.reason, "papers-meta research-reason"));
    if (record.inventory_url && /^\.\/(korean|english)\.html(?:\?modality=vision)?#inventory$/.test(record.inventory_url)) {
      const row = element("a", `표에서 보기: ${(record.changes || []).join(", ")} →`);
      row.href = record.inventory_url;
      const links = element("p", "", "papers-meta");
      links.append(row);
      article.append(links);
    }
    return article;
  }

  function renderResearch() {
    if (!research) return;
    const text = researchQuery.value.trim().toLocaleLowerCase();
    const stage = researchStage.value;
    const filtered = research.papers.filter(p => (!stage || p.stage === stage)
      && `${p.title} ${p.arxiv_id} ${p.reason}`.toLocaleLowerCase().includes(text));
    researchCount.textContent = `${filtered.length}건 / 전체 ${research.totals.papers}건`;
    researchList.hidden = false;
    researchList.replaceChildren(...filtered.slice(0, researchLimit).map(researchCard));
    if (!filtered.length) researchList.append(element("p", "조건에 맞는 논문이 없습니다."));
    researchMore.hidden = filtered.length <= researchLimit;
  }

  function renderDays(days) {
    const body = researchDays.querySelector("tbody");
    const recent = days.slice(-14).reverse();
    body.replaceChildren(...recent.map(day => {
      const row = element("tr");
      const cells = [day.day, day.abstracts, day.attempted, day.counts.pdf_failed, day.counts.draft_rejected,
        day.counts.excluded, day.counts.held, day.counts.awaiting, day.counts.published];
      cells.forEach((value, index) => {
        const cell = element(index ? "td" : "th", String(value));
        if (!index) cell.scope = "row";
        if (index === 8 && value) cell.className = "research-published";
        row.append(cell);
      });
      return row;
    }));
    researchDays.hidden = !recent.length;
  }

  researchQuery.addEventListener("input", () => { researchLimit = 50; renderResearch(); });
  researchStage.addEventListener("change", () => { researchLimit = 50; renderResearch(); });
  researchMore.addEventListener("click", () => { researchLimit += 50; renderResearch(); });
  fetch("./research-status.json", { cache: "no-cache" }).then(response => {
    if (!response.ok) throw new Error("Could not load research status");
    return response.json();
  }).then(data => {
    if (data.schema_version !== 1 || !Array.isArray(data.papers)) throw new Error("Invalid research status");
    research = data;
    const updated = document.querySelector("#research-updated");
    const run = data.last_run_at ? `최근 조사 ${date(data.last_run_at)}` : "";
    const status = data.run_status === "paused_time_budget" ? " · 시간 예산으로 중단, 다음 날 이어서 조사" : "";
    updated.textContent = `${run}${status} · 수집 ${data.totals.papers}건 · 대기 ${data.totals.queued}건 · 표 반영 ${data.totals.published}건`;
    for (const [id, label] of Object.entries(data.stages)) {
      const option = element("option", `${label} (${data.totals[id] ?? 0})`);
      option.value = id;
      researchStage.append(option);
    }
    renderDays(data.days);
    renderResearch();
  }).catch(() => {
    researchCount.textContent = "조사 현황을 불러오지 못했습니다. 잠시 후 새로고침해 주세요.";
  });
})();

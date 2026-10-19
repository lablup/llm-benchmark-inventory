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
})();

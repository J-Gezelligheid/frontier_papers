const DATA_URL = "standalone-policy-journal-tracker/data/policy_tracker.json";

const state = {
  data: null,
  topics: [],
  journals: [],
};

const els = {
  updateTime: document.getElementById("update-time"),
  refreshBtn: document.getElementById("refresh-btn"),
  topicFilter: document.getElementById("topic-filter"),
  journalFilter: document.getElementById("journal-filter"),
  searchInput: document.getElementById("search-input"),
  summaryCards: document.getElementById("summary-cards"),
  errorBox: document.getElementById("error-box"),
  journalList: document.getElementById("journal-list"),
};

function escapeHtml(input) {
  return String(input || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function normalize(input) {
  return String(input || "").toLowerCase().trim();
}

function paperMatchesFilter(paper) {
  const selectedTopic = els.topicFilter.value;
  const keyword = normalize(els.searchInput.value);

  if (selectedTopic) {
    const topics = Array.isArray(paper.matched_topics) ? paper.matched_topics : [];
    if (!topics.includes(selectedTopic)) {
      return false;
    }
  }

  if (!keyword) {
    return true;
  }

  const haystack = normalize(
    `${paper.title_en} ${paper.title_zh} ${paper.abstract_en} ${paper.abstract_zh} ${paper.matched_topics}`
  );
  return haystack.includes(keyword);
}

function journalMatchesFilter(journal) {
  const selectedJournal = els.journalFilter.value;
  if (!selectedJournal) {
    return true;
  }
  return journal.name === selectedJournal;
}

function renderSummary(journals) {
  const matched = journals.reduce((sum, journal) => sum + (journal.papers || []).length, 0);
  const total = journals.reduce((sum, journal) => sum + (journal.total_in_issue || 0), 0);
  const hasError = journals.filter((j) => j.error).length;

  els.summaryCards.innerHTML = `
    <article class="summary-card">
      <div class="summary-label">追踪期刊</div>
      <div class="summary-value">${journals.length}</div>
    </article>
    <article class="summary-card">
      <div class="summary-label">命中文章</div>
      <div class="summary-value">${matched}</div>
    </article>
    <article class="summary-card">
      <div class="summary-label">目录总量</div>
      <div class="summary-value">${total}</div>
    </article>
    <article class="summary-card">
      <div class="summary-label">采集异常期刊</div>
      <div class="summary-value">${hasError}</div>
    </article>
  `;
}

function renderJournals() {
  if (!state.data) {
    return;
  }

  const allJournals = state.journals.filter(journalMatchesFilter);
  const cards = [];

  for (const journal of allJournals) {
    const papers = (journal.papers || []).filter(paperMatchesFilter);
    const paperHtml = papers.length
      ? papers
          .map((paper) => {
            const topics = Array.isArray(paper.matched_topics) ? paper.matched_topics : [];
            const chips = topics
              .map((topic, i) => `<span class="chip chip-${i % 3}">${escapeHtml(topic)}</span>`)
              .join("");

            return `
              <article class="paper-item">
                <h3 class="paper-title"><a href="${escapeHtml(paper.url)}" target="_blank" rel="noopener">${escapeHtml(paper.title_en || "")}</a></h3>
                <div class="chip-row">${chips}</div>
                <p class="cn-title">中文标题：${escapeHtml(paper.title_zh || "暂无")}</p>
                <p class="abstract"><strong>Abstract (EN):</strong> ${escapeHtml(paper.abstract_en || "No abstract.")}</p>
                <p class="abstract"><strong>Abstract (ZH):</strong> ${escapeHtml(paper.abstract_zh || "暂无中文摘要。")}</p>
              </article>
            `;
          })
          .join("")
      : `<p class="empty-note">当前筛选条件下无结果。</p>`;

    cards.push(`
      <section class="journal-card">
        <div class="journal-header">
          <h2 class="journal-title">${escapeHtml(journal.name || "")}</h2>
          <div class="journal-meta">
            当前期次：<a href="${escapeHtml(journal.issue_url || "#")}" target="_blank" rel="noopener">${escapeHtml(journal.issue_title || "Latest issue")}</a>
            · 命中 ${Number(journal.matched_count || 0)} / ${Number(journal.total_in_issue || 0)}
          </div>
          ${journal.error ? `<div class="journal-error">提示：${escapeHtml(journal.error)}</div>` : ""}
        </div>
        <div class="paper-list">${paperHtml}</div>
      </section>
    `);
  }

  els.journalList.innerHTML = cards.length ? cards.join("") : `<p class="empty-note">没有匹配的期刊或文章。</p>`;
}

function fillFilterOptions() {
  els.topicFilter.innerHTML = `<option value="">全部主题</option>`;
  for (const topic of state.topics) {
    els.topicFilter.insertAdjacentHTML("beforeend", `<option value="${escapeHtml(topic)}">${escapeHtml(topic)}</option>`);
  }

  els.journalFilter.innerHTML = `<option value="">全部期刊</option>`;
  for (const journal of state.journals) {
    els.journalFilter.insertAdjacentHTML(
      "beforeend",
      `<option value="${escapeHtml(journal.name || "")}">${escapeHtml(journal.name || "")}</option>`
    );
  }
}

function showError(message) {
  els.errorBox.hidden = false;
  els.errorBox.textContent = message;
}

function clearError() {
  els.errorBox.hidden = true;
  els.errorBox.textContent = "";
}

async function loadData(showLoadingText = true) {
  if (showLoadingText) {
    els.updateTime.textContent = "加载中...";
  }
  clearError();

  try {
    const response = await fetch(`${DATA_URL}?t=${Date.now()}`, {
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    const policy = payload.policy_tracker || {};
    const journals = Array.isArray(policy.journals) ? policy.journals : [];
    const topics = Array.isArray(policy.topics) ? policy.topics : [];

    state.data = payload;
    state.journals = journals;
    state.topics = topics;

    fillFilterOptions();
    renderSummary(journals);
    renderJournals();

    const updatedAt = payload.updated_at ? `${payload.updated_at} UTC` : "未知";
    els.updateTime.textContent = `数据更新时间：${updatedAt}`;
  } catch (error) {
    els.updateTime.textContent = "数据加载失败";
    showError(`无法加载数据：${error.message}`);
    els.summaryCards.innerHTML = "";
    els.journalList.innerHTML = "";
  }
}

function bindEvents() {
  els.refreshBtn.addEventListener("click", () => loadData(false));
  els.topicFilter.addEventListener("change", renderJournals);
  els.journalFilter.addEventListener("change", renderJournals);
  els.searchInput.addEventListener("input", renderJournals);
}

bindEvents();
loadData(true);
setInterval(() => loadData(false), 5 * 60 * 1000);

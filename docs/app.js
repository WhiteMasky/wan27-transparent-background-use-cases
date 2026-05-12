const data = window.WAN27_DATA;

const kindFilter = document.querySelector("#kindFilter");
const statusFilter = document.querySelector("#statusFilter");
const categoryFilter = document.querySelector("#categoryFilter");
const caseList = document.querySelector("#caseList");

const rate = (success, total) => total ? `${Math.round((success / total) * 100)}%` : "0%";

document.querySelector("#overallRate").textContent = rate(data.stats.overall.success, data.stats.overall.total);
document.querySelector("#generationRate").textContent = rate(data.stats.generation.success, data.stats.generation.total);
document.querySelector("#editingRate").textContent = rate(data.stats.editing.success, data.stats.editing.total);

const categories = ["all", ...new Set(data.items.map((item) => item.category))];
categoryFilter.innerHTML = categories.map((category) => {
  const label = category === "all" ? "全部类别" : category;
  return `<option value="${category}">${label}</option>`;
}).join("");

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function pct(value) {
  return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "N/A";
}

function renderRefs(item) {
  if (!item.references || !item.references.length) return "";
  return `<div class="refs">${item.references.map((src) => `
    <div class="ref-frame"><img src="${src}" alt="${escapeHtml(item.id)} reference" loading="lazy"></div>
  `).join("")}</div>`;
}

function renderCard(item) {
  const status = item.success ? "成功" : "失败";
  const statusClass = item.success ? "success" : "fail";
  const type = item.kind === "generation" ? "透明背景生成" : "透明背景编辑";
  const image = item.preview || item.image;
  return `
    <article class="case-card" data-kind="${item.kind}" data-status="${statusClass}" data-category="${escapeHtml(item.category)}">
      <div class="media">
        <div class="image-frame">
          ${image ? `<img src="${image}" alt="${escapeHtml(item.id)} output" loading="lazy">` : ""}
        </div>
        ${renderRefs(item)}
      </div>
      <div class="case-body">
        <div class="case-head">
          <div>
            <h3 class="case-title">${escapeHtml(item.id)}</h3>
            <div class="meta">
              <span class="chip">${type}</span>
              <span class="chip">${escapeHtml(item.category)}</span>
              <span class="chip ${statusClass}">${status}</span>
              <span class="chip">透明像素 ${pct(item.transparentRatio)}</span>
            </div>
          </div>
        </div>
        ${item.effect ? `<p>${escapeHtml(item.effect)}</p>` : ""}
        <pre class="prompt"><code>${escapeHtml(item.prompt)}</code></pre>
      </div>
    </article>
  `;
}

function render() {
  const kind = kindFilter.value;
  const status = statusFilter.value;
  const category = categoryFilter.value;
  const filtered = data.items.filter((item) => {
    if (kind !== "all" && item.kind !== kind) return false;
    if (status === "success" && !item.success) return false;
    if (status === "fail" && item.success) return false;
    if (category !== "all" && item.category !== category) return false;
    return true;
  });
  caseList.innerHTML = filtered.map(renderCard).join("");
}

[kindFilter, statusFilter, categoryFilter].forEach((control) => {
  control.addEventListener("change", render);
});

render();

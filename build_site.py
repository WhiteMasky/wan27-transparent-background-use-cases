import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SITE = ROOT / "docs"
ASSETS = SITE / "assets"
SITE.mkdir(exist_ok=True)
ASSETS.mkdir(exist_ok=True)


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def copy_asset(path: str | None) -> str:
    if not path:
        return ""
    src = Path(path)
    if not src.is_absolute():
        src = ROOT / src
    if not src.exists() or not src.is_file():
        return ""
    target = ASSETS / src.name
    if target.resolve() != src.resolve():
        shutil.copy2(src, target)
    return f"assets/{target.name}"


def category_from_id(item_id: str, fallback: str = "") -> str:
    if fallback:
        return fallback
    prefixes = [
        ("poster_", "海报素材"),
        ("logo_", "Logo/标识"),
        ("clothing_", "衣服服饰"),
        ("anime_", "动漫人物"),
        ("real_model_", "真人模特"),
        ("product_", "商品"),
        ("ecommerce_", "电商商品"),
        ("food_", "餐饮素材"),
        ("fashion_", "衣服服饰"),
        ("character_", "角色贴纸"),
    ]
    for prefix, label in prefixes:
        if item_id.startswith(prefix):
            return label
    return "其他"


def effect_note(item_id: str) -> str:
    notes = {
        "wan_cutout_tshirt_recolor": "透明成功；蓝色换色完成，但保留整个人，不是只抠 T 恤。",
        "wan_food_menu_cutout_garnish": "透明成功；拉面抠图、加蛋和葱花完成。",
        "wan_car_cutout_paint": "透明成功；汽车改成金属青绿色并保留结构。",
        "wan_logo_emboss_preserve_alpha": "透明失败；Logo 质感化完成但背景不是真透明。",
        "wan_icon_tshirt_pattern": "透明成功；T 恤图标加闪电图案完成。",
        "wan_generated_model_outfit_edit": "透明成功；模特西装换红色 hoodie，姿态保持。",
        "wan_multi_food_poster_asset": "透明失败；完成海报风格拼接，但生成了射线/背景。",
        "wan_multi_car_logo_decal": "透明成功；车身贴花合成和抠图成功。",
    }
    return notes.get(item_id, "")


def pct(value) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.1f}%"
    return "N/A"


def build_data() -> dict:
    generation = []
    seen = set()
    for rel in ["transparent_bg_results/summary.json", "transparent_bg_complex21_results/summary.json"]:
        summary_path = ROOT / rel
        if not summary_path.exists():
            continue
        summary = load_json(rel)
        for item in summary["results"]:
            if item.get("model") != "wan2.7-image-pro":
                continue
            key = ("generation", item["id"])
            if key in seen:
                continue
            seen.add(key)
            generation.append(
                {
                    "kind": "generation",
                    "id": item["id"],
                    "category": category_from_id(item["id"]),
                    "success": bool(item.get("success")),
                    "transparentRatio": item.get("transparent_pixel_ratio"),
                    "nonOpaqueRatio": item.get("non_opaque_pixel_ratio"),
                    "image": copy_asset(item.get("file")),
                    "preview": copy_asset(item.get("preview")),
                    "prompt": item.get("prompt", ""),
                    "effect": "文本直出透明 PNG",
                }
            )

    edit_summary = load_json("transparent_edit_results/summary.json")
    editing = []
    for item in edit_summary["results"]:
        if item.get("model") != "wan2.7-image-pro":
            continue
        editing.append(
            {
                "kind": "editing",
                "id": item["id"],
                "category": item.get("category") or category_from_id(item["id"]),
                "success": bool(item.get("alpha_success")),
                "transparentRatio": item.get("transparent_pixel_ratio"),
                "nonOpaqueRatio": item.get("non_opaque_pixel_ratio"),
                "image": copy_asset(item.get("file")),
                "preview": copy_asset(item.get("preview")),
                "references": [copy_asset(path) for path in item.get("references", []) if copy_asset(path)],
                "prompt": item.get("prompt", ""),
                "effect": effect_note(item["id"]),
            }
        )

    all_items = generation + editing
    return {
        "generatedAt": "2026-05-12",
        "stats": {
            "generation": {
                "total": len(generation),
                "success": sum(1 for item in generation if item["success"]),
            },
            "editing": {
                "total": len(editing),
                "success": sum(1 for item in editing if item["success"]),
            },
            "overall": {
                "total": len(all_items),
                "success": sum(1 for item in all_items if item["success"]),
            },
        },
        "items": all_items,
    }


def write_site(data: dict) -> None:
    (SITE / "data.js").write_text(
        "window.WAN27_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    (SITE / "index.html").write_text(
        """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wan2.7 透明背景 Use Cases</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="hero">
    <nav class="topbar" aria-label="主导航">
      <div class="brand">
        <span class="brand-mark">α</span>
        <span>Wan2.7 Transparent Lab</span>
      </div>
      <a class="repo-link" href="#prompting">提示词技巧</a>
    </nav>
    <section class="hero-grid">
      <div>
        <h1>Wan2.7 透明背景生成与编辑案例库</h1>
        <p class="lead">把实测图片、参考图、成功率、提示词和透明 alpha 判定放到同一个可浏览页面，方便复用和横向比较。</p>
        <div class="hero-actions">
          <a class="primary" href="#cases">查看案例</a>
          <a class="secondary" href="#templates">复制模板</a>
        </div>
      </div>
      <div class="metric-panel" aria-label="测试指标">
        <div class="metric">
          <span id="overallRate">--</span>
          <small>总体透明成功率</small>
        </div>
        <div class="metric-row">
          <div><strong id="generationRate">--</strong><small>文本生成</small></div>
          <div><strong id="editingRate">--</strong><small>参考图编辑</small></div>
        </div>
      </div>
    </section>
  </header>

  <main>
    <section class="section summary">
      <div class="section-title">
        <h2>测试结论</h2>
        <p>Wan2.7 对文本直出透明 PNG 更稳定；参考图编辑也可用，但多图海报素材和 Logo 质感化更容易生成不透明背景。</p>
      </div>
      <div class="insight-grid">
        <article><h3>生成</h3><p>商品、服饰、动漫人物、真人模特和食物素材成功率高，提示词要强调 isolated asset 与 PNG alpha。</p></article>
        <article><h3>编辑</h3><p>抠图、换色、人物换装、车身贴花表现较好；复杂海报拼接要额外禁止装饰背景。</p></article>
        <article><h3>验收</h3><p>只看棋盘格预览不够，必须检查 PNG/RGBA 和透明像素比例，避免“假透明”。</p></article>
      </div>
    </section>

    <section class="section" id="cases">
      <div class="section-title split">
        <div>
          <h2>Use Case 表格</h2>
          <p>每条案例保留原提示词、透明像素比例和图片。编辑案例会展示参考图。</p>
        </div>
        <div class="filters" aria-label="筛选">
          <select id="kindFilter" aria-label="类型筛选">
            <option value="all">全部类型</option>
            <option value="generation">透明背景生成</option>
            <option value="editing">透明背景编辑</option>
          </select>
          <select id="statusFilter" aria-label="状态筛选">
            <option value="all">全部结果</option>
            <option value="success">只看成功</option>
            <option value="fail">只看失败</option>
          </select>
          <select id="categoryFilter" aria-label="类别筛选"></select>
        </div>
      </div>
      <div class="case-list" id="caseList"></div>
    </section>

    <section class="section prompting" id="prompting">
      <div class="section-title">
        <h2>确保完全透明的提示词工程</h2>
        <p>核心思路：把透明背景定义为文件输出约束，而不是视觉风格描述。</p>
      </div>
      <div class="rules">
        <article>
          <h3>生成时</h3>
          <ul>
            <li>写清楚 <code>real PNG</code> 与 <code>PNG alpha channel</code>。</li>
            <li>使用 <code>isolated asset</code>、<code>subject only</code>、<code>catalog cutout</code>。</li>
            <li>禁止 <code>checkerboard</code>、白底、灰底、场景、桌面、墙面和海报矩形。</li>
          </ul>
        </article>
        <article>
          <h3>编辑时</h3>
          <ul>
            <li>透明输入：要求 <code>preserve the exact existing alpha mask</code>。</li>
            <li>不透明输入：要求 <code>remove the original background completely</code>。</li>
            <li>多图拼接：用 <code>transparent asset cluster</code>，避免 <code>poster background</code>。</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="section templates" id="templates">
      <div class="section-title">
        <h2>推荐模板</h2>
      </div>
      <div class="template-grid">
        <article>
          <h3>透明背景生成</h3>
          <pre><code>Create a production-ready isolated asset as a real PNG with transparent background. The background must be fully transparent using the PNG alpha channel. Do not draw a checkerboard pattern, white canvas, gray canvas, colored backdrop, shadow box, scene, floor, wall, table, border, frame, or poster rectangle. Subject only, centered, clean cutout edges, natural antialiasing on edge pixels. Asset brief: [你的主体描述]</code></pre>
        </article>
        <article>
          <h3>透明背景编辑</h3>
          <pre><code>Edit Image 1: [具体编辑目标]. Return a real PNG with transparent background using the PNG alpha channel. If the input already has transparency, preserve the exact existing alpha mask outside the edited subject. If the input has an opaque background, remove it completely. Output only the edited subject, centered, clean antialiased cutout edges. No checkerboard, no white canvas, no gray canvas, no colored backdrop, no wall, no floor, no table, no scene, no frame, no poster rectangle, no decorative background.</code></pre>
        </article>
      </div>
    </section>
  </main>

  <footer>
    <span>Wan2.7 transparent background test archive</span>
    <span>Generated from local experiment data</span>
  </footer>
  <script src="data.js"></script>
  <script src="app.js"></script>
</body>
</html>
""",
        encoding="utf-8",
    )

    (SITE / "styles.css").write_text(
        """* {
  box-sizing: border-box;
}

:root {
  --bg: #f7f7f2;
  --ink: #151515;
  --muted: #65655f;
  --line: #d7d5c8;
  --surface: #ffffff;
  --surface-2: #efeee6;
  --accent: #0f766e;
  --accent-2: #bf3a30;
  --shadow: 0 20px 60px rgba(23, 23, 18, 0.12);
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  letter-spacing: 0;
}

a {
  color: inherit;
}

.hero {
  min-height: 88vh;
  padding: 28px clamp(18px, 4vw, 56px) 46px;
  background:
    linear-gradient(135deg, rgba(15, 118, 110, 0.18), rgba(255, 255, 255, 0) 36%),
    radial-gradient(circle at 82% 20%, rgba(191, 58, 48, 0.14), transparent 28%),
    var(--bg);
  border-bottom: 1px solid var(--line);
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  color: white;
  background: var(--ink);
}

.repo-link,
.primary,
.secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 18px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 760;
}

.repo-link,
.secondary {
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.62);
}

.primary {
  background: var(--ink);
  color: white;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(320px, 0.82fr);
  gap: clamp(30px, 6vw, 88px);
  align-items: end;
  max-width: 1180px;
  margin: 110px auto 0;
}

h1 {
  margin: 0;
  max-width: 820px;
  font-size: clamp(42px, 7vw, 92px);
  line-height: 0.95;
  letter-spacing: 0;
}

.lead {
  max-width: 680px;
  margin: 28px 0 0;
  color: var(--muted);
  font-size: clamp(18px, 2vw, 22px);
  line-height: 1.55;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 34px;
}

.metric-panel {
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 28px;
  box-shadow: var(--shadow);
}

.metric span {
  display: block;
  font-size: clamp(64px, 9vw, 112px);
  font-weight: 900;
  line-height: 0.9;
}

small {
  display: block;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.35;
}

.metric-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 28px;
  padding-top: 22px;
  border-top: 1px solid var(--line);
}

.metric-row strong {
  display: block;
  font-size: 32px;
}

.section {
  max-width: 1180px;
  margin: 0 auto;
  padding: 72px clamp(18px, 3vw, 34px);
}

.section-title {
  max-width: 760px;
  margin-bottom: 28px;
}

.section-title.split {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 22px;
  max-width: none;
}

h2 {
  margin: 0;
  font-size: clamp(30px, 4vw, 52px);
  line-height: 1.05;
}

h3 {
  margin: 0 0 12px;
  font-size: 20px;
}

.section-title p,
article p,
li {
  color: var(--muted);
  line-height: 1.65;
}

.insight-grid,
.rules,
.template-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.rules,
.template-grid {
  grid-template-columns: repeat(2, 1fr);
}

article {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 22px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

select {
  min-height: 42px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  color: var(--ink);
  padding: 0 36px 0 12px;
  font: inherit;
  font-weight: 650;
}

.case-list {
  display: grid;
  gap: 14px;
}

.case-card {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 20px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px;
}

.media {
  display: grid;
  gap: 10px;
}

.image-frame {
  display: grid;
  place-items: center;
  min-height: 260px;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  background:
    linear-gradient(45deg, #e6e6e6 25%, transparent 25%),
    linear-gradient(-45deg, #e6e6e6 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #e6e6e6 75%),
    linear-gradient(-45deg, transparent 75%, #e6e6e6 75%);
  background-size: 28px 28px;
  background-position: 0 0, 0 14px, 14px -14px, -14px 0;
}

.image-frame img {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
}

.refs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.ref-frame {
  min-height: 120px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 8px;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.ref-frame img {
  max-width: 100%;
  max-height: 140px;
  object-fit: contain;
}

.case-body {
  display: grid;
  align-content: start;
  gap: 14px;
}

.case-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 14px;
}

.case-title {
  margin: 0;
  font-size: 24px;
  line-height: 1.2;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--muted);
  font-size: 13px;
  font-weight: 740;
}

.chip.success {
  background: rgba(15, 118, 110, 0.12);
  color: var(--accent);
}

.chip.fail {
  background: rgba(191, 58, 48, 0.12);
  color: var(--accent-2);
}

.prompt {
  margin: 0;
  padding: 14px;
  border-radius: 8px;
  background: #171713;
  color: #f2f0e6;
  white-space: pre-wrap;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.55;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
}

footer {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 26px clamp(18px, 4vw, 56px);
  color: var(--muted);
  border-top: 1px solid var(--line);
}

@media (max-width: 900px) {
  .hero-grid,
  .case-card,
  .insight-grid,
  .rules,
  .template-grid {
    grid-template-columns: 1fr;
  }

  .hero-grid {
    margin-top: 72px;
  }

  .section-title.split {
    align-items: stretch;
    flex-direction: column;
  }

  .filters select {
    flex: 1 1 180px;
  }
}

@media (max-width: 560px) {
  .topbar,
  footer,
  .case-head {
    align-items: stretch;
    flex-direction: column;
  }

  .metric-row,
  .refs {
    grid-template-columns: 1fr;
  }
}
""",
        encoding="utf-8",
    )

    (SITE / "app.js").write_text(
        """const data = window.WAN27_DATA;

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
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    write_site(build_data())

#!/usr/bin/env python3
"""Write index.html from manifests. All scenes stay as recorded (Candidate)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CH_SVG = (
    '<svg viewBox="0 0 27 18" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="27" height="18" fill="#DA291C"/>'
    '<g fill="#fff"><rect x="11" y="3" width="5" height="12"/>'
    '<rect x="7.5" y="6.5" width="12" height="5"/></g></svg>'
)

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-FPVHCRLKD2"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-FPVHCRLKD2');
</script>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Jason D’s Vision — Switzerland</title>
  <link rel="canonical" href="https://devlij.github.io/jason-ds-vision-switzerland-preview/" />
  <meta name="description" content="AI-generated artistic interpretations of Switzerland. Free to use, no credit required." />
  <style>
    :root {
      --bg: #140d0d;
      --card: #201413;
      --text: #f7efec;
      --muted: #c4a9a2;
      --accent: #e0483e;
      --line: #4f2b28;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }
    a { color: var(--accent); }
    header, main, footer, .promise, #license {
      max-width: 1100px;
      margin: 0 auto;
      padding: 1.25rem 1.25rem;
    }
    .pointer {
      font-size: 0.95rem;
      color: var(--muted);
      border-bottom: 1px solid var(--line);
      padding-bottom: 1rem;
    }
    h1 {
      font-size: 1.75rem;
      font-weight: 650;
      margin: 1.25rem 0 0.35rem;
      letter-spacing: 0.01em;
      display: flex;
      align-items: center;
    }
    .country-switch {
      margin: 0.15rem 0 0.85rem;
      font-size: 0.95rem;
      color: var(--muted);
      letter-spacing: 0.01em;
    }
    .country-switch a { color: var(--accent); text-decoration: none; }
    .country-switch a:hover { text-decoration: underline; }
    .country-switch [aria-current="page"] { color: var(--text); font-weight: 600; }
    .country-switch .sep { margin: 0 0.45rem; color: var(--line); }
    .sub { color: var(--muted); margin: 0 0 1.5rem; }
    .promise h2, #license h2 { font-size: 1.2rem; margin-top: 2rem; }
    .promise p, #license p { color: var(--muted); max-width: 70ch; }
    .toolbar {
      display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; margin: 1.5rem 0 1rem;
    }
    .toolbar input, .toolbar select {
      background: var(--card); color: var(--text); border: 1px solid var(--line);
      border-radius: 8px; padding: 0.55rem 0.75rem; font: inherit;
    }
    .toolbar input { flex: 1 1 220px; min-width: 180px; }
    .toolbar button {
      background: transparent; color: var(--muted); border: 1px solid var(--line);
      border-radius: 8px; padding: 0.55rem 0.9rem; cursor: pointer; font: inherit;
    }
    .toolbar button:hover { color: var(--text); border-color: var(--muted); }
    #result-count { color: var(--muted); font-size: 0.9rem; }
    #no-results { display: none; color: var(--muted); padding: 2rem 0; text-align: center; }
    .grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1.25rem; margin-bottom: 2rem;
    }
    .card {
      background: var(--card); border: 1px solid var(--line); border-radius: 14px;
      overflow: hidden; display: flex; flex-direction: column;
    }
    .preview { position: relative; }
    .fmt-tabs {
      position: absolute; top: 1.05rem; left: 1.05rem; display: flex; gap: 6px; z-index: 2;
    }
    .fmt-tab {
      background: rgba(20, 13, 13, 0.82); color: var(--text); border: 1px solid var(--line);
      border-radius: 8px; padding: 5px 10px; font: inherit; font-size: 12px; line-height: 1.2; cursor: pointer;
    }
    .fmt-tab:hover { border-color: var(--muted); }
    .fmt-tab.is-active {
      background: var(--accent); border-color: var(--accent); color: var(--bg); font-weight: 700;
    }
    .view-affordance {
      position: absolute; top: 1.05rem; right: 1.05rem; z-index: 2;
      padding: 5px 10px; border: 1px solid rgba(255, 255, 255, 0.35); border-radius: 999px;
      background: rgba(20, 13, 13, 0.72); color: var(--text); font-size: 11px; pointer-events: none;
    }
    .thumb {
      display: block; padding: 0.65rem 0.65rem 0; background: #120c0c; line-height: 0;
    }
    .thumb img {
      width: 100%; height: auto; display: block; border-radius: 8px; background: #000;
      aspect-ratio: 16 / 9; object-fit: contain;
    }
    .thumb.tall img { aspect-ratio: 4 / 5; }
    .card-body { padding: 1rem 1rem 1.15rem; display: flex; flex-direction: column; gap: 0.35rem; flex: 1; }
    .entry-id { font-size: 0.75rem; letter-spacing: 0.06em; text-transform: uppercase; color: var(--accent); }
    .status-row { display: flex; flex-wrap: wrap; gap: 0.45rem; align-items: center; }
    .status {
      display: inline-block; font-size: 0.72rem; letter-spacing: 0.04em; text-transform: uppercase;
      border-radius: 999px; padding: 0.2rem 0.55rem; border: 1px solid var(--line); color: var(--muted);
    }
    .status.candidate { color: var(--muted); border-color: var(--line); }
    .caption { font-size: 1.05rem; font-weight: 600; margin: 0; }
    .scenario, .composition, .detail { font-size: 0.85rem; color: var(--muted); margin: 0; }
    .detail { font-size: 0.92rem; color: #f0e4df; margin: 0.35rem 0 0; }
    .actions { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.85rem; align-items: center; }
    .actions a.download {
      display: inline-block; text-decoration: none; background: #3a221f; color: var(--text);
      border-radius: 8px; padding: 0.4rem 0.7rem; font-size: 0.85rem; border: 1px solid var(--line);
    }
    .actions a.download:hover { border-color: var(--accent); }
    .badge {
      display: inline-block; font-size: 0.75rem; color: var(--bg); background: var(--accent);
      border-radius: 999px; padding: 0.25rem 0.6rem; text-decoration: none; font-weight: 600;
    }
    footer {
      border-top: 1px solid var(--line); color: var(--muted); font-size: 0.9rem; padding-bottom: 2.5rem;
    }
    footer .sig { color: var(--text); font-weight: 600; }
    .flag-band { height: 6px; background: #DA291C; }
    .flag { display: inline-block; width: 46px; height: 30px; border-radius: 4px; vertical-align: -4px; margin-right: 12px; box-shadow: 0 0 0 1px rgba(255,255,255,.25); overflow: hidden; flex: 0 0 auto; }
    .flag svg { display: block; width: 100%; height: 100%; }
    .flag-chip { display: inline-block; width: 22px; height: 15px; border-radius: 2px; vertical-align: -2px; margin-right: 6px; box-shadow: 0 0 0 1px rgba(255,255,255,.2); overflow: hidden; }
    .flag-chip svg { display: block; width: 100%; height: 100%; }
    .flag-chip.flag-de { background: linear-gradient(to bottom,#000 0 33.34%,#DD0000 0 66.67%,#FFCE00 0); }
    .flag-chip.flag-it { background: linear-gradient(to right,#009246 0 33.34%,#fff 0 66.67%,#CE2B37 0); }
    .flag-chip.flag-es { background: linear-gradient(to bottom,#AA151B 0 25%,#F1BF00 0 75%,#AA151B 0); }
    .flag-chip.flag-fr { background: linear-gradient(to right,#0055A4 0 33.34%,#fff 0 66.67%,#EF4135 0); }
    .flag-chip.flag-gr { background: repeating-linear-gradient(to bottom,#0D5EAF 0 3px,#fff 0 6px); }
    .flag-chip.flag-nl { background: linear-gradient(to bottom,#AE1C28 0 33.34%,#fff 0 66.67%,#21468B 0); }
    .lb { position: fixed; inset: 0; z-index: 60; display: none; align-items: center; justify-content: center; background: rgba(20, 13, 13, 0.93); }
    .lb.open { display: flex; }
    .lb figure { margin: 0; max-width: 94vw; }
    .lb img { max-width: 94vw; max-height: 80vh; display: block; border-radius: 6px; }
    .lb figcaption { display: flex; justify-content: space-between; gap: 16px; color: #f7efec; font-size: 14px; padding: 10px 2px 0; }
    .lb-count { color: #c4a9a2; white-space: nowrap; }
    .lb-close, .lb-prev, .lb-next { position: absolute; background: rgba(20, 13, 13, 0.85); color: #f7efec; border: 1px solid #4f2b28; border-radius: 999px; width: 46px; height: 46px; font-size: 20px; cursor: pointer; line-height: 1; }
    .lb-close { top: 14px; right: 14px; }
    .lb-prev { left: 12px; top: 50%; transform: translateY(-50%); }
    .lb-next { right: 12px; top: 50%; transform: translateY(-50%); }
    @media (max-width: 640px) { .lb-prev { left: 4px; } .lb-next { right: 4px; } }
  </style>
  <meta property="og:type" content="website"/>
  <meta property="og:site_name" content="Jason D's Vision"/>
  <meta property="og:title" content="Jason D's Vision — Switzerland"/>
  <meta property="og:description" content="AI-generated artistic interpretations of Switzerland. Free to use, no credit required."/>
  <meta property="og:image" content="https://devlij.github.io/jason-ds-vision-switzerland-preview/library/world/Switzerland/Zermatt/ch-01-001-16x9.png"/>
  <meta property="og:url" content="https://devlij.github.io/jason-ds-vision-switzerland-preview/"/>
  <meta name="twitter:card" content="summary_large_image"/>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ImageGallery",
  "name": "Jason D's Vision \u2014 Switzerland",
  "url": "https://devlij.github.io/jason-ds-vision-switzerland-preview/",
  "description": "AI-generated artistic interpretations of Switzerland. Free to use, no credit required.",
  "inLanguage": "en",
  "creator": {
    "@type": "Organization",
    "name": "Jason D's Vision"
  }
}
</script>
</head>
<body>
  <div class="flag-band" aria-hidden="true"></div>
  <header>
    <p class="pointer">Every image is free to use — no credit required. See <a href="#license">license</a> below.</p>
    <h1><span class="flag" aria-hidden="true">__CH_SVG__</span>Jason D’s Vision — Switzerland</h1>
    <nav class="country-switch" aria-label="Country galleries">
      <span aria-current="page"><span class="flag-chip" aria-hidden="true">__CH_SVG__</span>Switzerland</span><span class="sep" aria-hidden="true">|</span><a href="https://devlij.github.io/jason-ds-vision-germany/"><span class="flag-chip flag-de" aria-hidden="true"></span>Germany</a><span class="sep" aria-hidden="true">|</span><a href="https://devlij.github.io/jason-ds-vision-italy-preview/"><span class="flag-chip flag-it" aria-hidden="true"></span>Italy</a><span class="sep" aria-hidden="true">|</span><a href="https://devlij.github.io/jason-ds-vision-spain-preview/"><span class="flag-chip flag-es" aria-hidden="true"></span>Spain</a><span class="sep" aria-hidden="true">|</span><a href="https://devlij.github.io/jason-ds-vision-france-preview/"><span class="flag-chip flag-fr" aria-hidden="true"></span>France</a><span class="sep" aria-hidden="true">|</span><a href="https://devlij.github.io/jason-ds-vision-greece-preview/"><span class="flag-chip flag-gr" aria-hidden="true"></span>Greece</a><span class="sep" aria-hidden="true">|</span><a href="https://devlij.github.io/jason-ds-vision-netherlands-preview/"><span class="flag-chip flag-nl" aria-hidden="true"></span>Netherlands</a>
    </nav>
    <p class="sub">Preview gallery · Country → Region → City · Candidate scenes until an independent QC pass</p>
  </header>

  <section class="promise">
    <h2>Our promise to creators</h2>
    <p>Beautiful, realistic imagery should never stand between a creator and their work. Everything in this gallery is free to use — for any purpose, forever, with no credit required. We make these images so the people doing the work always have something stunning to build on.</p>
    <p><a href="#license">Read the full license</a></p>
  </section>

  <main>
    <div class="toolbar" role="search">
      <input id="q" type="search" placeholder="Search by city, site, or region" aria-label="Search by city, site, or region" />
      <select id="region" aria-label="Filter by region">
        <option value="">All regions</option>
      </select>
      <button type="button" id="clear">Clear</button>
      <span id="result-count"></span>
    </div>
    <div id="no-results">No scenes match that search.</div>
    <div class="grid" id="grid"></div>
  </main>

  <section id="license">
    <h2>License</h2>
    <p>Every image in Jason D's Vision is free to use for any purpose — personal or commercial. No credit is required. If you'd like to credit, 'Jason D's Vision' is appreciated, but it's entirely your choice.</p>
    <p>Jason D's Vision waives its own rights in these images. This doesn't waive anyone else's rights: if an image happens to include a trademark, logo, or other third-party material, those rights still belong to their owners. All images are AI-generated artistic interpretations, not photographs, and use of an image doesn't imply endorsement by Jason D's Vision.</p>
  </section>

  <footer>
    <p>AI-generated artistic interpretations · <span class="sig">Jason D’s Vision</span></p>
  </footer>

  <script>
    const SCENES = __SCENES__;

    const grid = document.getElementById('grid');
    const q = document.getElementById('q');
    const region = document.getElementById('region');
    const clearBtn = document.getElementById('clear');
    const countEl = document.getElementById('result-count');
    const noResults = document.getElementById('no-results');

    const regions = [...new Set(SCENES.map(s => s.region))].sort();
    for (const r of regions) {
      const opt = document.createElement('option');
      opt.value = r; opt.textContent = r; region.appendChild(opt);
    }

    function esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[ch]));
    }
    function fileName(url) {
      const path = String(url).split("?")[0];
      const slash = path.lastIndexOf("/");
      return slash >= 0 ? path.slice(slash + 1) : path;
    }

    function render() {
      const query = q.value.trim().toLowerCase();
      const reg = region.value;
      const filtered = SCENES.filter(s => {
        if (reg && s.region !== reg) return false;
        if (!query) return true;
        const hay = (s.city + ' ' + s.caption + ' ' + s.region + ' ' + s.entry_id).toLowerCase();
        return hay.includes(query);
      });
      grid.innerHTML = '';
      noResults.style.display = filtered.length ? 'none' : 'block';
      countEl.textContent = filtered.length + ' scene' + (filtered.length === 1 ? '' : 's');
      for (const s of filtered) {
        const card = document.createElement('article');
        card.className = 'card';
        const file16 = s.file_16x9;
        const file45 = s.file_4x5;
        const status = s.approval_status || 'Candidate';
        card.innerHTML = `
          <div class="preview">
            <div class="fmt-tabs" role="group" aria-label="Image size">
              <button type="button" class="fmt-tab is-active" data-format="16x9" aria-pressed="true">16:9</button>
              <button type="button" class="fmt-tab" data-format="4x5" aria-pressed="false">4:5</button>
            </div>
            <a class="thumb" href="${esc(file16)}">
              <img src="${esc(file16)}" alt="${esc(s.alt_text)}" loading="lazy" data-src-16="${esc(file16)}" data-src-45="${esc(file45)}" />
              <span class="view-affordance">View image</span>
            </a>
          </div>
          <div class="card-body">
            <div class="status-row">
              <div class="entry-id">${esc(s.entry_id)}</div>
              <span class="status candidate">${esc(status)}</span>
            </div>
            <h3 class="caption">${esc(s.caption)}</h3>
            <p class="scenario">Scenario: ${esc(s.scenario_label)}</p>
            <p class="composition">${esc(s.composition)}</p>
            ${s.description ? `<p class="detail">${esc(s.description)}</p>` : ""}
            <div class="actions">
              <a class="badge" href="${esc(s.license_anchor)}">${esc(s.license_badge)}</a>
              <a class="download" href="${esc(file16)}" download="${esc(fileName(file16))}">Download 16:9</a>
              <a class="download" href="${esc(file45)}" download="${esc(fileName(file45))}">Download 4:5</a>
            </div>
          </div>`;
        grid.appendChild(card);
      }
    }
    grid.addEventListener('click', (event) => {
      const tab = event.target.closest('.fmt-tab');
      if (!tab) return;
      event.preventDefault();
      event.stopPropagation();
      const card = tab.closest('.card');
      if (!card) return;
      const fmt = tab.dataset.format;
      card.querySelectorAll('.fmt-tab').forEach((item) => {
        const on = item === tab;
        item.classList.toggle('is-active', on);
        item.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      const link = card.querySelector('a.thumb');
      const img = link && link.querySelector('img');
      if (!img || !link) return;
      const next = fmt === '4x5' ? img.getAttribute('data-src-45') : img.getAttribute('data-src-16');
      if (next) {
        img.src = next;
        link.href = next;
      }
      link.classList.toggle('tall', fmt === '4x5');
    });
    q.addEventListener('input', render);
    region.addEventListener('change', render);
    clearBtn.addEventListener('click', () => { q.value = ''; region.value = ''; render(); });
    render();
  </script>
  <script>
  (function(){
    var overlay=document.createElement('div');
    overlay.className='lb';overlay.setAttribute('aria-hidden','true');
    overlay.innerHTML='<button class="lb-close" aria-label="Close">&times;</button>'
      +'<button class="lb-prev" aria-label="Previous image">&#8592;</button>'
      +'<figure><img alt=""><figcaption><span class="lb-cap"></span><span class="lb-count"></span></figcaption></figure>'
      +'<button class="lb-next" aria-label="Next image">&#8594;</button>';
    document.body.appendChild(overlay);
    var img=overlay.querySelector('img'),cap=overlay.querySelector('.lb-cap'),count=overlay.querySelector('.lb-count');
    var items=[],idx=0;
    function visibleCards(){return Array.prototype.filter.call(document.querySelectorAll('.card'),function(c){return c.style.display!=='none';});}
    function show(i){
      items=visibleCards().map(function(c){
        var a=c.querySelector('a.thumb');var t=c.querySelector('h3.caption');
        return{src:a?a.getAttribute('href'):'',cap:t?t.textContent:''};
      }).filter(function(x){return x.src;});
      if(!items.length)return;
      idx=(i+items.length)%items.length;
      img.src=items[idx].src;img.alt=items[idx].cap;cap.textContent=items[idx].cap;
      count.textContent=(idx+1)+' / '+items.length;
      overlay.classList.add('open');overlay.setAttribute('aria-hidden','false');document.body.style.overflow='hidden';
    }
    function hide(){overlay.classList.remove('open');overlay.setAttribute('aria-hidden','true');document.body.style.overflow='';}
    document.addEventListener('click',function(e){
      var tab=e.target.closest?e.target.closest('.fmt-tab'):null;
      if(tab)return;
      var a=e.target.closest?e.target.closest('a.thumb'):null;
      if(a){e.preventDefault();var cards=visibleCards();show(cards.indexOf(a.closest('.card')));return;}
      if(e.target===overlay||(e.target.closest&&e.target.closest('.lb-close')))hide();
      else if(e.target.closest&&e.target.closest('.lb-prev'))show(idx-1);
      else if(e.target.closest&&e.target.closest('.lb-next'))show(idx+1);
    });
    document.addEventListener('keydown',function(e){
      if(!overlay.classList.contains('open'))return;
      if(e.key==='Escape')hide();
      else if(e.key==='ArrowLeft')show(idx-1);
      else if(e.key==='ArrowRight')show(idx+1);
    });
  })();
  </script>
</body>
</html>
"""


def main() -> None:
    manifests = sorted((ROOT / "manifests").glob("CH-*.json"))
    scenes = [json.loads(path.read_text(encoding="utf-8")) for path in manifests]
    for scene in scenes:
        if scene.get("approval_status") != "Candidate":
            raise SystemExit(f"{scene['entry_id']} is not Candidate")
    payload = json.dumps(scenes, ensure_ascii=False, indent=2)
    html = PAGE.replace("__SCENES__", payload).replace("__CH_SVG__", CH_SVG)
    if "dataset.src45" in html or "dataset.src16" in html:
        raise SystemExit("refusing dataset.src accessors")
    if "getAttribute('data-src-45')" not in html and 'getAttribute("data-src-45")' not in html:
        raise SystemExit("missing data-src-45 getter")
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote index.html with {len(scenes)} scenes")


if __name__ == "__main__":
    main()

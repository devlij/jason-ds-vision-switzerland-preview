# Jason D's Vision — Switzerland Build Kit v1.0 (2026-09-24)

Self-contained kit for hired agent. Territory: Switzerland only (all 26 cantons). Target: 365 scenes.

## Mission
Original photorealistic AI artistic interpretations of real places. Free to use, no credit required. Optional credit "Jason D's Vision" appreciated.

## Scope
- Switzerland only. Do NOT touch Italy, France, Spain, Germany, Greece, Netherlands.
- Target 365 scenes matching Italy/France/Greece.
- Each scene = two masters: 1920×1080 (16:9) and 864×1080 (4:5).
- Repo (exists, Pages on): https://github.com/devlij/jason-ds-vision-switzerland-preview
- Live: https://devlij.github.io/jason-ds-vision-switzerland-preview/
- Push straight to origin/main (one PNG per commit preferred). Do NOT leave gallery updates only on a PR branch.
- Do NOT create a new repo. Do NOT use Netlify Drop.

## Brand (every image, baked in)
1. Caption: plain `<site>, <City>` bottom-left (e.g. "Chapel Bridge, Lucerne")
2. Scenario: `Scenario: 24 September 2026 · 14:30 Europe/Zurich` (full month name) — depicts real-time scenario, never implies on-site capture
3. Disclosure: "AI-generated artistic interpretation · Not a photograph."
4. Signature: exact **Jason D's Vision** (curly apostrophe U+2019) bottom-right
- Gradient scrim (fade up), never solid bar. Small subordinate text.
- Width-scaled fonts: caption .016, scenario .012, disclosure .010, signature .018

## Evidence card (before each generate)
Location/caption, camera viewpoint, 2 reference links, 3 geometry anchors, Open-Meteo weather (model data wording only), solar/time of day, independent description, source-use notes.

## Generation
- Real-time Europe/Zurich scenarios (day or night as actual). Weather = Open-Meteo current model data.
- Season-honest mountains. No invented scaffolding / restored buildings.
- Editorial quality target (never present as measured %).
- Text-prompt-only by default. All scenes stay **Candidate** until Cosmo QC.
- No prominent identifiable people; avoid logos/copyrighted art as focal subjects.

## Honest terminology
Never: "real-time conditions", "photograph/captured", "80%+ measured", "verified on-site" unless true, "Worldwide" for CH-only page.
Write: Open-Meteo model wording, artistic interpretation, editorial target, reported/modelled, "Jason D's Vision — Switzerland".

## Gates (5/5) before done
Visual/location, Technical (dims+text), Originality, Commercial/IP, Publication readiness. Stay Candidate.

## Files
- IDs: CH-01-001 … no gaps unexplained
- Paths: `library/world/Switzerland/<City>/ch-01-001-16x9.png` and `ch-01-001-4x5.png`
- approvals/CH-01-001.md, manifests/CH-01-001.json
- Manifest: country "Switzerland", region = canton, city = town only, 2–4 sentence description (Spain-style), alt_text, file paths, license badge

## Report line
**CH-01-001 — Matterhorn, Zermatt** · Scenario: … · Weather: model data from Open-Meteo … · Masters: … · Gates: 5/5 pass.

## Starter sequence (CH-01-001–016)
1. Matterhorn, Zermatt (Gornergrat view)
2. Chapel Bridge, Lucerne
3. Jungfrau panorama, Interlaken (Harder Kulm)
4. Jet d'Eau, Geneva
5. Old Town and Zytglogge, Bern
6. Bahnhofstrasse / Limmat, Zurich
7. Staubbach Falls, Lauterbrunnen
8. Medieval town and castle, Gruyères
9. Chillon Castle, Montreux
10. Lake and Engadin, St. Moritz
11. Village and Alpstein, Appenzell
12. Lakefront and Monte Brè, Lugano
13. Rhine and Mittlere Brücke, Basel
14. Castle and lake, Thun
15. Eiger north face, Grindelwald
16. Rhine Falls, Schaffhausen

Captions must be exact `<site>, <City>` form.

### 11b After starter — all 26 cantons
Expand every canton systematically (anchors in full kit). No canton left behind. Keep catalogue; no duplicates.

## Gallery (index.html) — required from first 3–4 scenes
- Top pointer, promise, license (exact copy from full kit)
- Country switcher: Switzerland | Germany | Italy | Spain | France | Greece | Netherlands with correct URLs
- Spain-style two-format cards: 16:9/4:5 tabs using getAttribute("data-src-45") / getAttribute("data-src-16"); Download 16:9 and Download 4:5; thumb link updates with tab
- Search by city/caption/region; clear; count; empty state
- Title: Jason D's Vision — Switzerland
- Footer: AI disclosure + Jason D's Vision signature

### Swiss flag visual identity (mandatory every regen)
1. First in body: `<div class="flag-band" aria-hidden="true"></div>` CSS height 6px background #DA291C
2. Palette: --bg:#140d0d; --card:#201413; --text:#f7efec; --muted:#c4a9a2; --accent:#e0483e; --line:#4f2b28;
3. h1 with CH SVG flag (exact SVG from kit) + title with curly apostrophe
4. Country switcher flag chips (CH SVG + gradient chips for DE/IT/ES/FR/GR/NL)

### Lightbox + OG (mandatory every regen)
- Lightbox with Switzerland palette; thumb class; ESC/arrows/backdrop; walks filtered cards; caption from h3.caption
- OG/Twitter metas pointing at published 16:9 master (Zermatt CH-01-001 once live)

## Push / publish
Push to origin/main on every finished scene so URL stays https://devlij.github.io/jason-ds-vision-switzerland-preview/
Preserve CNAME if present; kit does not require custom domain yet.

## Standing lessons from Greece/France lines
- Push batches directly to origin/main
- One image commit rhythm OK
- Never self-promote Candidate → Approved
- Auto-continue toward 365 after starter unless Jason stops you


## Exact license / promise / pointer copy

Top pointer: Every image is free to use — no credit required. See license below. (link → #license)

Promise heading: Our promise to creators
Promise body: Beautiful, realistic imagery should never stand between a creator and their work. Everything in this gallery is free to use — for any purpose, forever, with no credit required. We make these images so the people doing the work always have something stunning to build on.
Link: Read the full license → #license

License p1: Every image in Jason D's Vision is free to use for any purpose — personal or commercial. No credit is required. If you'd like to credit, 'Jason D's Vision' is appreciated, but it's entirely your choice.
License p2: Jason D's Vision waives its own rights in these images. This doesn't waive anyone else's rights: if an image happens to include a trademark, logo, or other third-party material, those rights still belong to their owners. All images are AI-generated artistic interpretations, not photographs, and use of an image doesn't imply endorsement by Jason D's Vision.

Country switcher URLs:
- Germany → https://devlij.github.io/jason-ds-vision-germany/
- Italy → https://devlij.github.io/jason-ds-vision-italy-preview/
- Spain → https://devlij.github.io/jason-ds-vision-spain-preview/
- France → https://devlij.github.io/jason-ds-vision-france-preview/
- Greece → https://devlij.github.io/jason-ds-vision-greece-preview/
- Netherlands → https://devlij.github.io/jason-ds-vision-netherlands-preview/

## CH SVG (exact)
<svg viewBox="0 0 27 18" xmlns="http://www.w3.org/2000/svg"><rect width="27" height="18" fill="#DA291C"/><g fill="#fff"><rect x="11" y="3" width="5" height="12"/><rect x="7.5" y="6.5" width="12" height="5"/></g></svg>

## OG block (exact, update og:image path if lead changes)
<meta property="og:type" content="website"/>
<meta property="og:site_name" content="Jason D's Vision"/>
<meta property="og:title" content="Jason D's Vision — Switzerland"/>
<meta property="og:description" content="AI-generated artistic interpretations of Switzerland. Free to use, no credit required."/>
<meta property="og:image" content="https://devlij.github.io/jason-ds-vision-switzerland-preview/library/world/Switzerland/Zermatt/ch-01-001-16x9.png"/>
<meta property="og:url" content="https://devlij.github.io/jason-ds-vision-switzerland-preview/"/>
<meta name="twitter:card" content="summary_large_image"/>

## Manifest example shape
entry_id, country Switzerland, region=canton, city, caption, scenario_label, composition, description (2-4 sentences), alt_text, file_16x9, file_4x5, license_badge Free · no credit needed, license_anchor #license

## Canton anchors (11b) — expand each fully
Zurich: old town Limmat Grossmünster Fraumünster, Bahnhofstrasse, Uetliberg, Rapperswil
Bern: old town Zytglogge Bundeshaus, Interlaken, Jungfrau region Grindelwald Lauterbrunnen Wengen Mürren, Thun, Brienz
Lucerne: Chapel Bridge Water Tower, Pilatus, Rigi, Weggis/Vitznau
Uri: Altdorf Tell, Andermatt, Gotthard Pass, Schöllenen Devil's Bridge
Schwyz: Schwyz town, Rütli, Mythen, Einsiedeln Abbey
Obwalden: Sarnen, Lungern, Titlis Engelberg
Nidwalden: Stans, Stanserhorn, Bürgenstock
Glarus: Glarus town, Klöntalersee
Zug: Zug old town lakefront
Fribourg: Fribourg old town, Gruyères, Murten
Solothurn: Solothurn St. Ursus, Weissenstein
Basel-Stadt: Rhine Mittlere Brücke Münster Rathaus
Basel-Landschaft: Augusta Raurica, Laufen
Schaffhausen: Rhine Falls, Munot, Stein am Rhein
Appenzell Ausserrhoden: Herisau, Urnäsch
Appenzell Innerrhoden: Appenzell village, Alpstein Säntis Seealpsee
St. Gallen: Abbey UNESCO exterior, Heiden, Werdenberg
Graubünden: St. Moritz Engadin, Bernina Lago Bianco, Davos, Landwasser Viaduct, Chur
Aargau: Aarau, Lenzburg Castle, Habsburg Castle
Thurgau: Frauenfeld, Arenenberg, Steckborn Untersee
Ticino: Lugano Monte Brè, Locarno Piazza Grande Madonna del Sasso, Bellinzona castles, Ascona
Vaud: Montreux Chillon, Lausanne cathedral Ouchy, Lavaux, Vevey
Valais: Zermatt Matterhorn Gornergrat, Saas-Fee, Aletsch, Sion Valère
Neuchâtel: Neuchâtel old town lake, La Chaux-de-Fonds, Creux du Van
Geneva: Jet d'Eau, St. Pierre, Carouge
Jura: Delémont, St-Ursanne, Doubs

Coverage: finish canton anchors before next, but same evidence/manifest standard always.

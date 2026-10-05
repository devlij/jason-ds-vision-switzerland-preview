#!/usr/bin/env python3
"""Switzerland gallery Night button (moon), format by format.

Same gate as the Spain and Italy night toggles, adapted to this catalogue.

A format is a night master only when that exact path is the scene's own
master, the file is already in this repo (or named as a file on the gallery
host, which serves this repo), and the manifest marks the scene night:

  * ``time_of_day`` is exactly Night, or
  * the composition head (text before ``·``) is Night or contains the whole
    word "night", or
  * ``alt_text`` contains the whole word "night", or
  * the ``qc_status`` tail after the last ``·`` is exactly Night.

``daylight_variant.source_night`` names the published master for almost every
scene, including afternoon daylight plates. That record alone is not a night
mark. Scenario hour is not used, so dawn, dusk, twilight, and moonlight plates
stay without a Night button unless one of the marks above is present.

A missing format stays empty. A 16:9 file, a daylight plate, and a postcard
plate are never copied into another night slot. A ``source_night`` path that
is not the scene's own master is never shown. The card still opens on its
current hero. Daylight, Postcard, and 360/Motion turn Night off, and Night
turns those off.

    python3 tools/night_toggle.py
    python3 tools/night_toggle.py --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
TEMPLATE = Path(__file__).resolve().parent / "gallery_template.html"
GALLERY_ORIGIN = "https://devlij.github.io/jason-ds-vision-switzerland-preview/"

FORMATS = (("16x9", "file_16x9"), ("4x5", "file_4x5"), ("9x16", "file_9x16"))
NIGHT_KEYS = ("file_16x9_night", "file_4x5_night", "file_9x16_night")
NIGHT_WORD = re.compile(r"\bnight\b", re.I)
ENTRY_RE = re.compile(r"^CH-\d{2}-\d{3}$")
BLOCKED_NAME = re.compile(r"daylight|postcard", re.I)

CSS_OLD = """    .day-tab.is-active {
      background: #e8b23a; border-color: #e8b23a; color: #1a1405; font-weight: 700;
    }
"""
CSS_NEW = """    .night-tab {
      display: inline-block; background: #243049; color: var(--text);
      border-radius: 8px; padding: 0.4rem 0.7rem; font-size: 0.85rem; border: 1px solid var(--line);
      cursor: pointer; font: inherit; margin-right: 0.35rem;
    }
    .night-tab:hover { border-color: var(--accent); }
    .night-tab.is-active {
      background: #1b2744; border-color: #9eb6e0; color: #e7eefc; font-weight: 700;
    }
    .fmt-tab:disabled, .fmt-tab.is-disabled { opacity: 0.4; cursor: default; }
"""

CONST_OLD = "        const dayReady = !!day16 && (!file45 || !!day45) && (!file916 || !!day916);\n"
CONST_NEW = """        const night16 = s.file_16x9_night || "";
        const night45 = s.file_4x5_night || "";
        const night916 = s.file_9x16_night || "";
        const hasNight = !!(night16 || night45 || night916);
"""

IMG_OLD = '(day916 ? ` data-src-916-day="${esc(day916)}"` : "");'
IMG_NEW = (
    '(day916 ? ` data-src-916-day="${esc(day916)}"` : "") +\n'
    '          (night16 ? ` data-src-16-night="${esc(night16)}"` : "") +\n'
    '          (night45 ? ` data-src-45-night="${esc(night45)}"` : "") +\n'
    '          (night916 ? ` data-src-916-night="${esc(night916)}"` : "");'
)

ROW_OLD = (
    '${dayReady ? `<div class="day-row"><button type="button" class="day-tab" '
    'data-daynight="night" aria-pressed="false" title="Toggle the daylight variant">'
    '\\u2600 Daylight</button></div>` : ""}'
)
ROW_NEW = (
    '${(hasNight || dayReady) ? `<div class="day-row">'
    '${hasNight ? `<button type="button" class="night-tab" aria-pressed="false" '
    'title="Show the night image">\\uD83C\\uDF19 Night</button>` : ""}'
    '${dayReady ? `<button type="button" class="day-tab" data-daynight="night" '
    'aria-pressed="false" title="Toggle the daylight variant">\\u2600 Daylight</button>` : ""}'
    '</div>` : ""}'
)

SRC_OLD = """      var im=a.querySelector('img');
      if(lbDay==='day'&&im){"""
SRC_NEW = """      var im=a.querySelector('img');
      if(im&&card.querySelector('.night-tab.is-active')){
        var nk=fmt==='4x5'?'data-src-45-night':fmt==='9x16'?'data-src-916-night':'data-src-16-night';
        var ns=im.getAttribute(nk);
        if(ns)return ns;
      }
      if(lbDay==='day'&&im){"""

LISTEN_ANCHOR = "    q.addEventListener('input', render);\n"
LISTENER = r"""    /* CH_NIGHT_TOGGLE START */
    function nightAttr(fmt) {
      return fmt === '4x5' ? 'data-src-45-night' : fmt === '9x16' ? 'data-src-916-night' : 'data-src-16-night';
    }
    function sceneAttr(fmt) {
      return fmt === '4x5' ? 'data-src-45' : fmt === '9x16' ? 'data-src-916' : 'data-src-16';
    }
    function stopCardMotionForNight(card) {
      var video = card.querySelector('video.motion-clip');
      if (video) { video.pause(); video.remove(); }
      var link = card.querySelector('a.thumb');
      if (link) link.hidden = false;
      card.querySelectorAll('.motion.is-active, .motion-btn.is-active, .motion-tab.is-active').forEach(function (btn) {
        btn.classList.remove('is-active');
        btn.setAttribute('aria-pressed', 'false');
      });
    }
    function showRecordedScenario(card) {
      var sc = card.querySelector('p.scenario');
      if (sc && sc.getAttribute('data-scenario')) sc.textContent = 'Scenario: ' + sc.getAttribute('data-scenario');
    }
    function enable916(card) {
      var tab = card.querySelector('.fmt-tab[data-format="9x16"]');
      if (!tab) return;
      tab.disabled = false;
      tab.classList.remove('is-disabled');
    }
    function applyNightImage(card, fmt) {
      var link = card.querySelector('a.thumb');
      var img = link && link.querySelector('img');
      if (!img || !link) return false;
      var next = img.getAttribute(nightAttr(fmt));
      if (!next) return false;
      img.src = next;
      link.href = next;
      link.classList.toggle('tall', fmt === '4x5');
      link.classList.toggle('tall916', fmt === '9x16');
      return true;
    }
    function applyNightDownloads(card) {
      var img = card.querySelector('a.thumb img');
      card.querySelectorAll('a.download').forEach(function (a) {
        var fmt = a.getAttribute('data-dl') || '16x9';
        var url = img && img.getAttribute(nightAttr(fmt));
        if (url) {
          a.hidden = false;
          a.href = url;
          a.setAttribute('download', url.split('/').pop());
        } else {
          a.hidden = true;
        }
      });
    }
    function showSceneDownloads(card) {
      var img = card.querySelector('a.thumb img');
      card.querySelectorAll('a.download').forEach(function (a) {
        var fmt = a.getAttribute('data-dl') || '16x9';
        var url = img && img.getAttribute(sceneAttr(fmt));
        if (url) {
          a.hidden = false;
          a.href = url;
          a.setAttribute('download', url.split('/').pop());
        }
      });
    }
    function restoreSceneImage(card) {
      var link = card.querySelector('a.thumb');
      var img = link && link.querySelector('img');
      var active = card.querySelector('.fmt-tab.is-active');
      var fmt = active ? active.getAttribute('data-format') : '16x9';
      if (!img || !link) return;
      var next = img.getAttribute(sceneAttr(fmt));
      if (!next) return;
      img.src = next;
      link.href = next;
      link.classList.toggle('tall', fmt === '4x5');
      link.classList.toggle('tall916', fmt === '9x16');
    }
    function activateNight(card) {
      stopCardMotionForNight(card);
      var sun = card.querySelector('.day-tab:not(.pc-tab)');
      if (sun) {
        sun.classList.remove('is-active');
        sun.setAttribute('aria-pressed', 'false');
        sun.setAttribute('data-daynight', 'night');
      }
      var postcard = card.querySelector('.pc-tab');
      if (postcard) {
        postcard.classList.remove('is-active');
        postcard.setAttribute('aria-pressed', 'false');
        postcard.setAttribute('data-postcard', 'off');
      }
      var night = card.querySelector('.night-tab');
      if (night) {
        night.classList.add('is-active');
        night.setAttribute('aria-pressed', 'true');
      }
      var img = card.querySelector('a.thumb img');
      var portrait = card.querySelector('.fmt-tab[data-format="9x16"]');
      var portraitOk = !!(img && img.getAttribute('data-src-916-night'));
      if (portrait) {
        portrait.disabled = !portraitOk;
        portrait.classList.toggle('is-disabled', !portraitOk);
      }
      var active = card.querySelector('.fmt-tab.is-active');
      var fmt = active ? active.getAttribute('data-format') : '16x9';
      if (!img || !img.getAttribute(nightAttr(fmt))) {
        var fallback = card.querySelector('.fmt-tab[data-format="16x9"]') || card.querySelector('.fmt-tab[data-format="4x5"]');
        if (fallback) {
          fmt = fallback.getAttribute('data-format');
          card.querySelectorAll('.fmt-tab').forEach(function (tab) {
            var on = tab === fallback;
            tab.classList.toggle('is-active', on);
            tab.setAttribute('aria-pressed', on ? 'true' : 'false');
          });
        }
      }
      applyNightImage(card, fmt);
      applyNightDownloads(card);
      showRecordedScenario(card);
    }
    function deactivateNight(card, restoreImage) {
      var night = card.querySelector('.night-tab');
      if (!night || !night.classList.contains('is-active')) return;
      night.classList.remove('is-active');
      night.setAttribute('aria-pressed', 'false');
      enable916(card);
      showSceneDownloads(card);
      if (restoreImage) {
        restoreSceneImage(card);
        showRecordedScenario(card);
      }
    }
    grid.addEventListener('click', function (event) {
      var card = event.target.closest && event.target.closest('.card');
      if (!card || !grid.contains(card)) return;
      var nightBtn = event.target.closest('.night-tab');
      if (nightBtn && card.contains(nightBtn)) {
        event.preventDefault();
        event.stopPropagation();
        activateNight(card);
        return;
      }
      var fmtTab = event.target.closest('.fmt-tab');
      if (fmtTab && card.querySelector('.night-tab.is-active')) {
        event.preventDefault();
        event.stopPropagation();
        if (fmtTab.disabled || fmtTab.classList.contains('is-disabled')) return;
        stopCardMotionForNight(card);
        var fmt = fmtTab.getAttribute('data-format');
        if (!applyNightImage(card, fmt)) return;
        card.querySelectorAll('.fmt-tab').forEach(function (tab) {
          var on = tab === fmtTab;
          tab.classList.toggle('is-active', on);
          tab.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
        applyNightDownloads(card);
        return;
      }
      var off = event.target.closest('.day-tab, .pc-tab, .motion, .motion-btn, .motion-tab');
      if (!off || off.classList.contains('night-tab')) return;
      var turningDaylight = off.classList.contains('day-tab') && !off.classList.contains('pc-tab');
      deactivateNight(card, !turningDaylight);
    }, true);
    /* CH_NIGHT_TOGGLE END */
"""


def clean_path(value: object) -> str:
    if not isinstance(value, str):
        return ""
    text = value.split("?", 1)[0].strip()
    if text.startswith(GALLERY_ORIGIN):
        text = text[len(GALLERY_ORIGIN) :]
    if not text or text.startswith(("/", "\\")) or ".." in text.replace("\\", "/"):
        return ""
    if "://" in text:
        return ""
    return text


def master_exists(rel: str) -> bool:
    rel = clean_path(rel)
    if not rel:
        return False
    path = (ROOT / rel).resolve()
    root = ROOT.resolve()
    if path != root and root not in path.parents:
        return False
    return path.is_file() and path.stat().st_size > 0


def lighting_is_night(scene: dict) -> bool:
    """Manifest lighting label, not the scenario clock and not source_night."""
    if str(scene.get("time_of_day") or "").strip() == "Night":
        return True
    head = str(scene.get("composition") or "").split("·", 1)[0].strip()
    if head in {"Night", "NIGHT"} or NIGHT_WORD.search(head):
        return True
    if NIGHT_WORD.search(str(scene.get("alt_text") or "")):
        return True
    qc = str(scene.get("qc_status") or "").strip()
    tail = re.split(r"\s*·\s*", qc)[-1].strip() if qc else ""
    return tail == "Night"


def _blocked_name(rel: str) -> bool:
    return bool(BLOCKED_NAME.search(Path(rel).name))


def night_urls(scene: dict, exists=master_exists) -> list[str]:
    """Return [16:9, 4:5, 9:16]. Empty string means that format has no night master."""
    if not lighting_is_night(scene):
        return ["", "", ""]
    variant = scene.get("daylight_variant")
    source = variant.get("source_night") if isinstance(variant, dict) else None
    if not isinstance(source, dict):
        source = {}
    found: list[str] = []
    for fmt, key in FORMATS:
        own = clean_path(scene.get(key))
        info = source.get(fmt)
        recorded = clean_path(info.get("path")) if isinstance(info, dict) else ""
        qualified = ""
        # A source_night path that is not this master is never shown.
        if recorded and recorded != own:
            recorded = ""
        if own and exists(own) and not _blocked_name(own):
            qualified = own
        found.append(qualified)
    return found


def attach_night_masters(scene: dict, source: dict, exists=master_exists) -> None:
    """Copy qualifying night paths onto a gallery scene. Omit empty formats."""
    for key, url in zip(NIGHT_KEYS, night_urls(source, exists)):
        if url:
            scene[key] = url
        else:
            scene.pop(key, None)


def load_manifests() -> list[dict]:
    found: list[dict] = []
    for path in sorted((ROOT / "manifests").glob("CH-*.json")):
        scene = json.loads(path.read_text(encoding="utf-8"))
        entry_id = scene.get("entry_id") or ""
        if ENTRY_RE.fullmatch(entry_id) and scene.get("caption"):
            found.append(scene)
    return found


def load_night_masters(scenes: list[dict] | None = None) -> dict[str, list[str]]:
    rows = scenes if scenes is not None else load_manifests()
    found: dict[str, list[str]] = {}
    for scene in rows:
        urls = night_urls(scene)
        if any(urls):
            found[str(scene["entry_id"])] = urls
    return found


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def upgrade_shell(text: str) -> str:
    """Add the Night button, attributes, and click handler. Idempotent."""
    if ".night-tab.is-active" not in text:
        text = _replace_once(text, CSS_OLD, CSS_OLD + CSS_NEW, "night css")
    if "const night16" not in text:
        text = _replace_once(text, CONST_OLD, CONST_OLD + CONST_NEW, "night consts")
    if "data-src-16-night" not in text:
        text = _replace_once(text, IMG_OLD, IMG_NEW, "night image attrs")
    if 'class="night-tab"' not in text:
        text = _replace_once(text, ROW_OLD, ROW_NEW, "night button")
    if "CH_NIGHT_TOGGLE START" not in text:
        text = _replace_once(text, LISTEN_ANCHOR, LISTENER + LISTEN_ANCHOR, "night click")
    src_at = text.find("function cardSrc")
    src_body = text[src_at : src_at + 900] if src_at >= 0 else ""
    if "data-src-45-night" not in src_body:
        text = _replace_once(text, SRC_OLD, SRC_NEW, "night lightbox")
    # An empty night src used to drop the card from the lightbox list.
    # A missing 9:16 night portrait falls through to the non-night image.
    buggy = (
        "        var nk=fmt==='4x5'?'data-src-45-night':fmt==='9x16'?'data-src-916-night':'data-src-16-night';\n"
        "        return im.getAttribute(nk)||'';\n"
    )
    fixed = (
        "        var nk=fmt==='4x5'?'data-src-45-night':fmt==='9x16'?'data-src-916-night':'data-src-16-night';\n"
        "        var ns=im.getAttribute(nk);\n"
        "        if(ns)return ns;\n"
    )
    if buggy in text:
        text = _replace_once(text, buggy, fixed, "lightbox night fallback")
    return text


def inject_night_fields(html: str, night: dict[str, list[str]]) -> str:
    """Add per-format night paths to SCENES. Does not rewrite other fields."""
    html = re.sub(r'\n    "file_(?:16x9|4x5|9x16)_night": "[^"]*",', "", html)
    for entry_id, urls in night.items():
        lines = []
        for key, url in zip(NIGHT_KEYS, urls):
            if url:
                lines.append(f"    {json.dumps(key)}: {json.dumps(url)},")
        if not lines:
            continue
        needle = f'"entry_id": "{entry_id}",'
        count = html.count(needle)
        if count != 1:
            raise SystemExit(f"{entry_id}: expected 1 scene record, found {count}")
        html = html.replace(needle, needle + "\n" + "\n".join(lines), 1)
    return html


def extract_scenes(html: str) -> list[dict]:
    marker = "const SCENES = "
    start_at = html.find(marker)
    if start_at < 0:
        raise SystemExit("SCENES missing from index.html")
    start = html.find("[", start_at)
    depth = 0
    for index in range(start, len(html)):
        char = html[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return json.loads(html[start : index + 1])
    raise SystemExit("SCENES array is not closed")


def _self_test() -> None:
    files = {
        "ch-night-16x9.png",
        "ch-night-4x5.png",
        "ch-night-9x16.png",
        "ch-day-16x9.png",
        "ch-dusk-16x9.png",
        "ch-dawn-16x9.png",
        "ch-moon-16x9.png",
        "ch-foreign-16x9.png",
    }

    def exists(rel: str) -> bool:
        return clean_path(rel) in files

    marked = {
        "time_of_day": "",
        "qc_status": "Approved · Cosmo QC 5/5 · Night",
        "composition": "Valley floor · note",
        "alt_text": "A place",
        "file_16x9": "ch-night-16x9.png",
        "file_4x5": "ch-night-4x5.png",
        "daylight_variant": {
            "source_night": {
                "16x9": {"path": "ch-night-16x9.png"},
                "4x5": {"path": "ch-night-4x5.png"},
            }
        },
    }
    if night_urls(marked, exists) != ["ch-night-16x9.png", "ch-night-4x5.png", ""]:
        raise SystemExit("self-test invented a 9:16 night plate")

    portrait = dict(marked)
    portrait["alt_text"] = "The ridge at night"
    portrait["qc_status"] = "Approved"
    portrait["file_9x16"] = "ch-night-9x16.png"
    if night_urls(portrait, exists)[2] != "ch-night-9x16.png":
        raise SystemExit("self-test dropped a named 9:16 night master")

    afternoon = {
        "qc_status": "Approved · Cosmo QC 5/5 · Daylight",
        "composition": "Terrace looking southwest · note",
        "alt_text": "A daytime terrace",
        "scenario_label": "1 October 2026 · 14:20 Europe/Zurich",
        "file_16x9": "ch-day-16x9.png",
        "file_4x5": "ch-night-4x5.png",
        "file_9x16": "ch-night-9x16.png",
        "daylight_variant": {
            "source_night": {
                "16x9": {"path": "ch-day-16x9.png"},
                "4x5": {"path": "ch-night-4x5.png"},
                "9x16": {"path": "ch-night-9x16.png"},
            }
        },
    }
    if any(night_urls(afternoon, exists)):
        raise SystemExit("self-test gave an afternoon plate a Night button")

    dusk = {
        "qc_status": "Approved · Cosmo QC 5/5 · Daylight",
        "composition": "Village at dusk · note",
        "alt_text": "Dusk over the church",
        "file_16x9": "ch-dusk-16x9.png",
        "daylight_variant": {"source_night": {"16x9": {"path": "ch-dusk-16x9.png"}}},
    }
    if any(night_urls(dusk, exists)):
        raise SystemExit("self-test gave a dusk plate a Night button")

    dawn = {
        "qc_status": "Approved · Cosmo QC 5/5 · Daylight",
        "composition": "Harbour at dawn · note",
        "alt_text": "Dawn on the quay",
        "file_16x9": "ch-dawn-16x9.png",
    }
    if any(night_urls(dawn, exists)):
        raise SystemExit("self-test gave a dawn plate a Night button")

    moon = {
        "qc_status": "Approved",
        "composition": "Moonlight on the lake · note",
        "alt_text": "Moonlight over the water",
        "file_16x9": "ch-moon-16x9.png",
        "daylight_variant": {"source_night": {"16x9": {"path": "ch-moon-16x9.png"}}},
    }
    if any(night_urls(moon, exists)):
        raise SystemExit("self-test gave a moonlight plate a Night button")

    marked_dusk = dict(dusk)
    marked_dusk["qc_status"] = "Approved · Cosmo QC 5/5 · Night"
    if night_urls(marked_dusk, exists)[0] != "ch-dusk-16x9.png":
        raise SystemExit("self-test ignored a dusk plate the manifest marks night")

    foreign = dict(marked)
    foreign["daylight_variant"] = {"source_night": {"16x9": {"path": "ch-foreign-16x9.png"}}}
    got = night_urls(foreign, exists)
    if got[0] != "ch-night-16x9.png" or "foreign" in " ".join(got):
        raise SystemExit("self-test showed a source_night path that is not the scene master")

    missing = dict(marked)
    missing["file_16x9"] = "ch-missing-16x9.png"
    missing["daylight_variant"] = {"source_night": {"16x9": {"path": "ch-missing-16x9.png"}}}
    if night_urls(missing, exists)[0]:
        raise SystemExit("self-test accepted a night master that is not on disk")

    daylight_name = dict(marked)
    daylight_name["file_16x9"] = "ch-night-daylight-16x9.png"
    daylight_name["daylight_variant"] = {
        "source_night": {"16x9": {"path": "ch-night-daylight-16x9.png"}}
    }
    files.add("ch-night-daylight-16x9.png")
    if night_urls(daylight_name, exists)[0]:
        raise SystemExit("self-test used a daylight file as a night master")

    escaped = dict(marked)
    escaped["file_16x9"] = "../ch-night-16x9.png"
    escaped["daylight_variant"] = {"source_night": {"16x9": {"path": "../ch-night-16x9.png"}}}
    if night_urls(escaped, exists)[0]:
        raise SystemExit("self-test accepted a path outside the repository")

    portrait_only = {
        "qc_status": "Approved · Cosmo QC 5/5 · Night",
        "file_16x9": "ch-night-16x9.png",
        "file_4x5": "ch-night-4x5.png",
    }
    if night_urls(portrait_only, exists)[2]:
        raise SystemExit("self-test filled 9:16 from a 16:9 master")


def check_html(html: str, template: str, night: dict[str, list[str]]) -> dict:
    _self_test()
    if "CH_NIGHT_TOGGLE START" not in html or 'class="night-tab"' not in html:
        raise SystemExit("index.html is missing the Night button")
    if "CH_NIGHT_TOGGLE START" not in template or 'class="night-tab"' not in template:
        raise SystemExit("gallery template is missing the Night button")
    if "Cosmo QC" in LISTENER or "Cosmo QC" in CSS_NEW or "Cosmo QC" in ROW_NEW:
        raise SystemExit("night toggle adds Cosmo QC text")
    handler = html.split("CH_NIGHT_TOGGLE START", 1)[1].split("CH_NIGHT_TOGGLE END", 1)[0]
    if "data-src-16')" in handler or "data-src-916')" in handler or "data-src-45')" in handler:
        raise SystemExit("night click handler falls back to a daylight or scene master")
    if "return im.getAttribute(nk)||''" in html or "return im.getAttribute(nk)||''" in template:
        raise SystemExit("lightbox drops a night card that has no plate for this format")
    scenes = extract_scenes(html)
    errors: list[str] = []
    buttons = 0
    counts = [0, 0, 0]
    seen: set[str] = set()
    for scene in scenes:
        entry_id = scene.get("entry_id") or ""
        if entry_id in seen:
            errors.append(f"duplicate card {entry_id}")
        seen.add(entry_id)
        urls = night.get(entry_id, ["", "", ""])
        got = [scene.get(key) or "" for key in NIGHT_KEYS]
        if got != urls:
            errors.append(f"{entry_id} night fields {got} != {urls}")
        if any(got):
            buttons += 1
        for index, url in enumerate(got):
            if not url:
                continue
            counts[index] += 1
            if not master_exists(url):
                errors.append(f"{entry_id} night master is not on disk: {url}")
            if _blocked_name(url):
                errors.append(f"{entry_id} night master is a daylight or postcard file: {url}")
            if index == 2 and url == got[0]:
                errors.append(f"{entry_id} 9:16 night plate repeats the 16:9 file")
            if index == 2 and "9x16" not in url:
                errors.append(f"{entry_id} 9:16 night plate is not a portrait path")
    missing = [entry_id for entry_id in night if entry_id not in seen]
    if missing:
        errors.append("night scenes missing from the gallery: " + ", ".join(missing[:8]))
    if errors:
        raise SystemExit("\n".join(errors[:30]))
    return {
        "cards": len(scenes),
        "night_buttons": buttons,
        "night_16x9": counts[0],
        "night_4x5": counts[1],
        "night_9x16": counts[2],
        "without_night": len(scenes) - buttons,
    }


def rebuild() -> dict:
    _self_test()
    original = INDEX.read_text(encoding="utf-8")
    template = TEMPLATE.read_text(encoding="utf-8")
    before_cosmo = len(re.findall(r"Cosmo QC", original))
    before_status = re.findall(r'"approval_status": "[^"]*"', original)
    before_art50 = len(re.findall(r"Art\.?\s*50", original))
    night = load_night_masters()
    updated = inject_night_fields(upgrade_shell(original), night)
    updated_template = upgrade_shell(template)
    if upgrade_shell(updated) != updated or inject_night_fields(updated, night) != updated:
        raise SystemExit("night toggle rebuild is not idempotent")
    if upgrade_shell(updated_template) != updated_template:
        raise SystemExit("template rebuild is not idempotent")
    if len(re.findall(r"Cosmo QC", updated)) != before_cosmo:
        raise SystemExit("night toggle changed a Cosmo QC claim")
    if re.findall(r'"approval_status": "[^"]*"', updated) != before_status:
        raise SystemExit("night toggle rewrote approval_status")
    if len(re.findall(r"Art\.?\s*50", updated)) != before_art50:
        raise SystemExit("night toggle changed an Art.50 line")
    if updated != original:
        INDEX.write_text(updated, encoding="utf-8")
    if updated_template != template:
        TEMPLATE.write_text(updated_template, encoding="utf-8")
    return check_html(updated, updated_template, night)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when the built page disagrees with the night-master gate.",
    )
    args = parser.parse_args()
    if args.check:
        census = check_html(
            INDEX.read_text(encoding="utf-8"),
            TEMPLATE.read_text(encoding="utf-8"),
            load_night_masters(),
        )
    else:
        census = rebuild()
    print(
        "cards {cards}, night buttons {night_buttons}, "
        "night 16:9 {night_16x9}, night 4:5 {night_4x5}, night 9:16 {night_9x16}, "
        "without night {without_night}".format(**census)
    )


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)

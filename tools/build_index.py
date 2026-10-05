#!/usr/bin/env python3
"""Write index.html from manifests.

The gallery shell (analytics, flag, badges, format tabs, downloads, lightbox,
word of the day, and the Phase-1 filters) lives in tools/gallery_template.html.
This script fills scene records and the Phase-1 related-scene table so a
rebuild keeps that behavior instead of reverting to an older page.

Phase-1, ported from the Spain pilot Jason signed off:
  search + region, plus day/night and mood (Coastal / Mountain / Urban / Historic);
  a live result count and a control that clears every filter;
  four related thumbnails (same region first, then shared mood tags, then id);
  Copy link with Copied feedback;
  id="<ENTRY_ID>" deep links.
A master that is not a real file is left out of the scene record and out of
the related-scene table, so the page never renders a control or thumb for it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
TEMPLATE = TOOLS / "gallery_template.html"
TAGS = TOOLS / "phase1_tags.json"

ENTRY_RE = re.compile(r"^CH-\d{2}-\d{3}$")
MOODS = ("coastal", "mountain", "urban", "historic")
PUBLIC_FIELDS = (
    "entry_id",
    "country",
    "region",
    "city",
    "caption",
    "scenario_label",
    "composition",
    "description",
    "alt_text",
    "file_16x9",
    "file_4x5",
    "license_badge",
    "license_anchor",
    "approval_status",
)
OPTIONAL_FILES = (
    "file_9x16",
    "file_16x9_day",
    "file_4x5_day",
    "file_9x16_day",
)

PHASE1_MARKERS = (
    'id="q"',
    'id="region"',
    'id="f-daynight"',
    'id="f-mood"',
    'id="clear"',
    'id="result-count"',
    "option value=\"coastal\">Coastal",
    "function relatedFor",
    "Copy link",
    "Copied \\u2713",
    "card.id = s.entry_id",
    "G-PDJ4WSS725",
    "getAttribute('data-src-45')",
)


def master_exists(path: str) -> bool:
    if not path or not isinstance(path, str):
        return False
    if path.startswith(("/", "\\")) or "://" in path:
        return False
    file_path = (ROOT / path).resolve()
    try:
        file_path.relative_to(ROOT.resolve())
    except ValueError:
        return False
    return file_path.is_file() and file_path.stat().st_size > 0


def _entry_sort_key(entry_id: str) -> tuple[int, str]:
    match = ENTRY_RE.fullmatch(entry_id or "")
    if not match:
        return (10**9, entry_id or "")
    return (int(entry_id.rsplit("-", 1)[-1]), entry_id)


def load_manifests() -> list[dict]:
    found: list[dict] = []
    for path in sorted((ROOT / "manifests").glob("CH-*.json")):
        scene = json.loads(path.read_text(encoding="utf-8"))
        entry_id = scene.get("entry_id") or ""
        if not ENTRY_RE.fullmatch(entry_id) or not scene.get("caption"):
            continue
        found.append(scene)
    found.sort(key=lambda scene: _entry_sort_key(scene["entry_id"]))
    return found


def load_tags() -> dict[str, dict]:
    raw = json.loads(TAGS.read_text(encoding="utf-8"))
    tags: dict[str, dict] = {}
    for entry_id, row in raw.items():
        if not ENTRY_RE.fullmatch(entry_id):
            raise SystemExit(f"phase1 tag id is not a scene id: {entry_id}")
        daynight = row.get("daynight") or infer_daynight(row)
        if daynight not in ("day", "night"):
            raise SystemExit(f"{entry_id} daynight must be day or night")
        moods = row.get("moods") or ""
        parts = [part for part in moods.split(",") if part]
        unknown = [part for part in parts if part not in MOODS]
        if unknown:
            raise SystemExit(f"{entry_id} unknown mood tags: {unknown}")
        tags[entry_id] = {"daynight": daynight, "moods": ",".join(parts)}
    return tags


def infer_daynight(scene: dict) -> str:
    label = str(scene.get("scenario_label") or "")
    match = re.search(r"(\d{1,2}):(\d{2})", label)
    if match:
        hour = int(match.group(1))
        return "night" if hour >= 18 or hour < 6 else "day"
    text = f"{scene.get('description') or ''} {scene.get('alt_text') or ''}".lower()
    if "below the horizon" in text or " at night" in text:
        return "night"
    return "day"


def image_alt(scene: dict) -> str:
    """Gallery img alt: `{caption} — {site}, {City}`.

    The descriptive caption is alt_text. The place title is the scene caption,
    which is already `site, City` (for example "Matterhorn, Zermatt").
    """
    place = str(scene.get("caption") or "").strip()
    caption = str(scene.get("alt_text") or "").strip()
    if caption and place:
        return f"{caption} — {place}"
    return caption or place


def publishable_scenes(manifests: list[dict], exists=master_exists) -> list[dict]:
    scenes: list[dict] = []
    for source in manifests:
        scene: dict = {}
        for field in PUBLIC_FIELDS:
            if field in ("file_16x9", "file_4x5"):
                path = source.get(field) or ""
                if exists(path):
                    scene[field] = path
                continue
            if field in source:
                scene[field] = source[field]
        for field in OPTIONAL_FILES:
            path = source.get(field) or ""
            if exists(path):
                scene[field] = path
        # Daylight masters are recorded under daylight_variant.files, not as
        # top-level file_*_day keys. Publish both formats only when each file
        # is on disk, so the card never offers a control for a missing master.
        if "file_16x9_day" not in scene or "file_4x5_day" not in scene:
            day16, day45 = daylight_pair(source)
            if exists(day16) and exists(day45):
                scene["file_16x9_day"] = day16
                scene["file_4x5_day"] = day45
        # 9:16 daylight is required before the gallery shows the daylight
        # button on any card that already has a 9:16 master.
        if "file_9x16_day" not in scene and scene.get("file_9x16"):
            day916 = daylight_916(source)
            if exists(day916):
                scene["file_9x16_day"] = day916
        # Static-ambient clips are optional. The card shows Motion only when
        # the 10s 4:5 file is on disk.
        motion = f"assets/{source['entry_id'].lower()}-motion-10s-4x5.mp4"
        if exists(motion):
            scene["file_motion_4x5"] = motion
        scene["image_alt"] = image_alt(source)
        scenes.append(scene)
    return scenes


def _daylight_files(source: dict) -> dict:
    variant = source.get("daylight_variant")
    if not isinstance(variant, dict):
        return {}
    files = variant.get("files")
    if not isinstance(files, dict):
        return {}
    return files


def daylight_pair(source: dict) -> tuple[str, str]:
    files = _daylight_files(source)
    return str(files.get("16x9") or ""), str(files.get("4x5") or "")


def daylight_916(source: dict) -> str:
    return str(_daylight_files(source).get("9x16") or "")


def phase1_meta(scenes: list[dict], tags: dict[str, dict], exists=master_exists) -> dict:
    """entry_id -> [region, day|night, mood-tags, 16x9 thumb, caption, image alt].

    Scenes whose 16:9 master is missing are omitted, so related thumbs and the
    day/night and mood filters never point at a file that is not on disk.
    """
    meta: dict[str, list] = {}
    for scene in scenes:
        thumb = scene.get("file_16x9") or ""
        if not exists(thumb):
            continue
        entry_id = scene["entry_id"]
        tag = tags.get(entry_id) or {}
        meta[entry_id] = [
            scene.get("region") or "",
            tag.get("daynight") or infer_daynight(scene),
            tag.get("moods") or "",
            thumb,
            scene.get("caption") or "",
            scene.get("image_alt") or image_alt(scene),
        ]
    return meta


def related_ids(meta: dict, entry_id: str, limit: int = 4) -> list[str]:
    """Same region first, then shared mood tags, then entry id. Deterministic."""
    me = meta.get(entry_id)
    if not me or not me[3]:
        return []
    mine = [part for part in (me[2] or "").split(",") if part]
    ranked: list[tuple[int, int, str]] = []
    for other_id, other in meta.items():
        if other_id == entry_id or not other[3]:
            continue
        other_moods = "," + (other[2] or "") + ","
        shared = sum(1 for part in mine if f",{part}," in other_moods)
        if other[0] == me[0] or shared > 0:
            ranked.append((0 if other[0] == me[0] else 1, -shared, other_id))
    ranked.sort()
    return [item[2] for item in ranked[:limit]]


def render_index(scenes: list[dict], meta: dict) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    if "__SCENES__" not in template or "__PHASE1_META__" not in template:
        raise SystemExit("gallery template is missing Phase-1 placeholders")
    scenes_json = json.dumps(scenes, ensure_ascii=False, indent=2)
    meta_json = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
    html = template.replace("__SCENES__", scenes_json).replace("__PHASE1_META__", meta_json)
    if "__SCENES__" in html or "__PHASE1_META__" in html:
        raise SystemExit("gallery placeholders were not filled")
    assert_phase1(html)
    return html


def assert_phase1(html: str) -> None:
    if "dataset.src45" in html or "dataset.src16" in html:
        raise SystemExit("refusing dataset.src accessors")
    missing = [marker for marker in PHASE1_MARKERS if marker not in html]
    if missing:
        raise SystemExit("regenerated gallery is missing Phase-1 markers: " + ", ".join(missing))
    if "if (!o || !o[3]) continue" not in html:
        raise SystemExit("related thumbs are not guarded against missing masters")
    if "const file16 = s.file_16x9 || \"\"" not in html:
        raise SystemExit("card render does not skip a missing 16:9 master")


def main() -> None:
    manifests = load_manifests()
    tags = load_tags()
    scenes = publishable_scenes(manifests)
    meta = phase1_meta(scenes, tags)
    html = render_index(scenes, meta)
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote index.html with {len(scenes)} scenes and {len(meta)} phase-1 records")
    from build_image_sitemap import write_sitemap

    stats = write_sitemap()
    print(
        "wrote image-sitemap.xml "
        f"scenes={stats['scenes']} images={stats['images']} "
        f"16:9={stats['formats']['16:9']} 4:5={stats['formats']['4:5']} 9:16={stats['formats']['9:16']}"
    )


if __name__ == "__main__":
    main()

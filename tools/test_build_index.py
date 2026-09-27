#!/usr/bin/env python3
"""Prove the gallery generator keeps Phase-1 and skips missing masters."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import build_index as gallery  # noqa: E402


def test_publishable_scenes_match_recorded_fields() -> None:
    scenes = gallery.publishable_scenes(gallery.load_manifests())
    assert len(scenes) == 365
    assert scenes[0]["entry_id"] == "CH-01-001"
    assert scenes[-1]["entry_id"] == "CH-01-365"
    assert all(scene["entry_id"] != "CH-01-05" for scene in scenes)
    assert scenes[0]["approval_status"] == "Candidate"
    assert gallery.master_exists(scenes[0]["file_16x9"])
    assert gallery.master_exists(scenes[0]["file_4x5"])


def test_related_is_region_first_then_mood_then_id() -> None:
    scenes = gallery.publishable_scenes(gallery.load_manifests())
    meta = gallery.phase1_meta(scenes, gallery.load_tags())
    related = gallery.related_ids(meta, "CH-01-001")
    assert len(related) == 4
    assert related == gallery.related_ids(meta, "CH-01-001")
    regions = [meta[item][0] for item in related]
    assert regions == ["Valais", "Valais", "Valais", "Valais"]
    # Same region and the same single mood tag, so the tie breaks on id.
    assert related == sorted(related)
    empty = gallery.related_ids(meta, "CH-01-106")
    assert len(empty) == 4
    assert all(meta[item][0] == meta["CH-01-106"][0] for item in empty)


def test_missing_master_is_omitted_from_scene_and_related() -> None:
    scenes = gallery.publishable_scenes(gallery.load_manifests())
    tags = gallery.load_tags()
    target = scenes[0]["file_16x9"]
    blocked = {target}

    def exists(path: str) -> bool:
        return path not in blocked and gallery.master_exists(path)

    published = gallery.publishable_scenes(gallery.load_manifests(), exists)
    assert "file_16x9" not in published[0]
    assert published[0]["file_4x5"]
    meta = gallery.phase1_meta(published, tags, exists)
    assert "CH-01-001" not in meta
    for row in meta.values():
        assert row[3] != target
        assert exists(row[3])
    # A neighbor still gets four thumbs, and none of them are the missing master.
    sample = gallery.related_ids(meta, "CH-01-017")
    assert len(sample) == 4
    assert "CH-01-001" not in sample


def test_regenerated_html_keeps_phase1_and_is_stable() -> None:
    scenes = gallery.publishable_scenes(gallery.load_manifests())
    meta = gallery.phase1_meta(scenes, gallery.load_tags())
    html = gallery.render_index(scenes, meta)
    again = gallery.render_index(scenes, meta)
    assert html == again
    assert "card.id = s.entry_id" in html
    assert "CH-01-001" in html
    missing = dict(scenes[0])
    missing.pop("file_16x9")
    missing.pop("file_4x5")
    lean = gallery.render_index([missing], {})
    payload = json.loads(lean.split("const SCENES = ", 1)[1].split(";\n", 1)[0])
    assert payload[0]["entry_id"] == "CH-01-001"
    assert "file_16x9" not in payload[0]
    assert "file_4x5" not in payload[0]
    assert "var SWITZERLAND_META = {};" in lean


def test_daylight_pair_is_published_only_when_both_masters_exist() -> None:
    scenes = gallery.publishable_scenes(gallery.load_manifests())
    by_id = {scene["entry_id"]: scene for scene in scenes}
    lit = by_id["CH-01-297"]
    assert lit["file_16x9_day"].endswith("ch-01-297-daylight-16x9.png")
    assert lit["file_4x5_day"].endswith("ch-01-297-daylight-4x5.png")
    assert gallery.master_exists(lit["file_16x9_day"])
    assert gallery.master_exists(lit["file_4x5_day"])
    assert "file_16x9_day" not in by_id["CH-01-001"]
    assert lit["approval_status"] == "Approved"

    def exists(path: str) -> bool:
        return path.endswith("ch-01-297-daylight-16x9.png")

    published = gallery.publishable_scenes(gallery.load_manifests(), exists)
    partial = {scene["entry_id"]: scene for scene in published}["CH-01-297"]
    assert "file_16x9_day" not in partial
    assert "file_4x5_day" not in partial


def test_status_class_follows_approval_status_text() -> None:
    scenes = gallery.publishable_scenes(gallery.load_manifests())
    html = gallery.render_index(scenes, gallery.phase1_meta(scenes, gallery.load_tags()))
    assert 'class="status ${esc(status.toLowerCase())}"' in html
    assert 'class="status candidate"' not in html
    assert "dataset.src45" not in html
    # Approval text is copied through, not rewritten. CH-01-001 stays the
    # weather rework's Candidate status.
    assert scenes[0]["approval_status"] == "Candidate"


def test_page_javascript_matches_python_related_order() -> None:
    scenes = gallery.publishable_scenes(gallery.load_manifests())
    meta = gallery.phase1_meta(scenes, gallery.load_tags())
    html = gallery.render_index(scenes, meta)
    script = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('function relatedFor');
const end = html.indexOf('function phase1Enhance');
const fn = html.slice(start, end);
const metaStart = html.indexOf('var SWITZERLAND_META = ');
const metaEnd = html.indexOf(';', metaStart);
const SWITZERLAND_META = JSON.parse(html.slice(metaStart + 'var SWITZERLAND_META = '.length, metaEnd));
eval(fn + '\nmodule.exports = {relatedFor, SWITZERLAND_META};');
"""
    # eval of the page function needs the function to close. relatedFor ends before phase1Enhance.
    runner = Path("/tmp/related_check.js")
    runner.write_text(
        """
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const start = html.indexOf('function relatedFor');
const end = html.indexOf('/* Per-card injection');
if (start < 0 || end < 0) throw new Error('relatedFor not found');
const metaStart = html.indexOf('var SWITZERLAND_META = ');
const metaEnd = html.indexOf(';', metaStart);
const SWITZERLAND_META = JSON.parse(html.slice(metaStart + 'var SWITZERLAND_META = '.length, metaEnd));
const relatedFor = new Function('SWITZERLAND_META', html.slice(start, end) + '\\nreturn relatedFor;')(SWITZERLAND_META);
const ids = JSON.parse(process.argv[3]);
const out = {};
for (const id of ids) out[id] = relatedFor(id);
process.stdout.write(JSON.stringify(out));
""",
        encoding="utf-8",
    )
    ids = ["CH-01-001", "CH-01-106", "CH-01-225", "CH-01-365"]
    completed = subprocess.run(
        ["node", str(runner), "/dev/stdin", json.dumps(ids)],
        input=html,
        text=True,
        check=True,
        capture_output=True,
    )
    page = json.loads(completed.stdout)
    for entry_id in ids:
        assert page[entry_id] == gallery.related_ids(meta, entry_id), entry_id
    runner.unlink()


def main() -> None:
    test_publishable_scenes_match_recorded_fields()
    test_related_is_region_first_then_mood_then_id()
    test_missing_master_is_omitted_from_scene_and_related()
    test_daylight_pair_is_published_only_when_both_masters_exist()
    test_status_class_follows_approval_status_text()
    test_regenerated_html_keeps_phase1_and_is_stable()
    test_page_javascript_matches_python_related_order()
    print("phase-1 generator tests passed")


if __name__ == "__main__":
    main()

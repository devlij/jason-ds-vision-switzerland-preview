#!/usr/bin/env python3
"""The image sitemap lists live Approved masters only."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import build_image_sitemap as images  # noqa: E402
import build_index as gallery  # noqa: E402

SITEMAP = "http://www.sitemaps.org/schemas/sitemap/0.9"
IMAGE = "http://www.google.com/schemas/sitemap-image/1.1"
HELD = [
    "CH-01-301",
    "CH-01-302",
    "CH-01-309",
    "CH-01-345",
    "CH-01-354",
    "CH-01-364",
    "CH-01-365",
]
# Weather reworks CH-01-001–087 are Candidate again. They stay out of the sitemap.
WEATHER = [f"CH-01-{number:03d}" for number in range(1, 88)]


def test_approved_records_skip_candidates_and_count_formats() -> None:
    records = images.approved_image_records()
    assert len(records) == 271
    counts = images.format_counts(records)
    assert counts == {"16:9": 271, "4:5": 271, "9:16": 0}
    ids = [record["entry_id"] for record in records]
    assert ids == sorted(ids, key=gallery._entry_sort_key)
    assert ids[0] == "CH-01-088"
    for entry_id in WEATHER + HELD:
        assert entry_id not in ids
    for stub in ("CH-01-05", "CH-01-06", "CH-01-07", "CH-01-08", "CH-01-09"):
        assert stub not in ids
    first = records[0]
    assert first["loc"] == "https://devlij.github.io/jason-ds-vision-switzerland-preview/#CH-01-088"
    assert first["title"] == "Bahnhofstrasse, Zurich"
    assert first["geo_location"] == "Zurich, Switzerland"
    assert first["caption"].startswith("AI-generated artistic interpretation of Bahnhofstrasse")
    assert [image["format"] for image in first["images"]] == ["16:9", "4:5"]
    assert first["images"][0]["loc"].startswith("https://devlij.github.io/jason-ds-vision-switzerland-preview/")
    assert " " not in first["images"][0]["loc"]
    neuchatel = next(record for record in records if record["entry_id"] == "CH-01-209")
    assert "Neuch%C3%A2tel" in neuchatel["images"][0]["loc"]
    assert neuchatel["title"] == "Neuchâtel lakefront, Neuchâtel"
    assert neuchatel["geo_location"] == "Neuchâtel, Switzerland"
    for record in records:
        manifest = next(scene for scene in gallery.load_manifests() if scene["entry_id"] == record["entry_id"])
        assert manifest["approval_status"] == "Approved"


def test_rendered_xml_is_well_formed_and_matches_records() -> None:
    records = images.approved_image_records()
    xml = images.render_sitemap(records)
    root = ET.fromstring(xml)
    assert root.tag == f"{{{SITEMAP}}}urlset"
    urls = list(root)
    assert len(urls) == 271
    assert urls[0].find(f"{{{SITEMAP}}}loc").text.endswith("#CH-01-088")
    blocks = urls[0].findall(f"{{{IMAGE}}}image")
    assert len(blocks) == 2
    assert blocks[0].find(f"{{{IMAGE}}}title").text == "Bahnhofstrasse, Zurich"
    assert blocks[0].find(f"{{{IMAGE}}}geo_location").text == "Zurich, Switzerland"
    assert blocks[0].find(f"{{{IMAGE}}}caption").text == records[0]["caption"]
    for entry_id in WEATHER + HELD:
        assert f"#{entry_id}" not in xml
    assert all(record["loc"].startswith(images.CANONICAL) for record in records)
    assert "file_16x9_day" not in xml
    assert "daylight" not in xml


def test_gallery_alts_use_caption_and_place() -> None:
    scenes = gallery.publishable_scenes(gallery.load_manifests())
    html = gallery.render_index(scenes, gallery.phase1_meta(scenes, gallery.load_tags()))
    expected = scenes[0]["image_alt"]
    assert expected.endswith(" — Matterhorn, Zermatt")
    assert expected in html
    assert 'alt="${esc(s.image_alt)}"' in html
    held = next(scene for scene in scenes if scene["entry_id"] == "CH-01-301")
    assert held["approval_status"] == "Candidate"
    assert held["image_alt"].endswith(" — " + held["caption"])
    weather = next(scene for scene in scenes if scene["entry_id"] == "CH-01-001")
    assert weather["approval_status"] == "Candidate"
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap: https://devlij.github.io/jason-ds-vision-switzerland-preview/sitemap.xml" in robots
    assert "Sitemap: https://devlij.github.io/jason-ds-vision-switzerland-preview/image-sitemap.xml" in robots


def main() -> None:
    test_approved_records_skip_candidates_and_count_formats()
    test_rendered_xml_is_well_formed_and_matches_records()
    test_gallery_alts_use_caption_and_place()
    print("image sitemap tests passed")


if __name__ == "__main__":
    main()

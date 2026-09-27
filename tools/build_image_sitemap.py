#!/usr/bin/env python3
"""Write image-sitemap.xml from live Approved scene manifests.

Candidates stay out, including open re-render ids that are still Candidate.
Each Approved scene with at least one master on disk becomes one <url> at the
canonical gallery URL plus the copy-link fragment (#ENTRY_ID). Each existing
16:9, 4:5, and 9:16 master becomes one <image:image>.

  image:caption      descriptive caption (manifest alt_text)
  image:title        site, City (manifest caption)
  image:geo_location City, Country
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_index as gallery  # noqa: E402

CANONICAL = "https://devlij.github.io/jason-ds-vision-switzerland-preview/"
SITEMAP_PATH = ROOT / "image-sitemap.xml"
MASTER_FIELDS = (
    ("file_16x9", "16:9"),
    ("file_4x5", "4:5"),
    ("file_9x16", "9:16"),
)


def absolute_asset_url(path: str) -> str:
    return CANONICAL + quote(path, safe="/")


def page_url(entry_id: str) -> str:
    return f"{CANONICAL}#{entry_id}"


def xml_text(value: str) -> str:
    return escape(value, entities={'"': "&quot;", "'": "&apos;"})


def approved_image_records(manifests: list[dict] | None = None, exists=gallery.master_exists) -> list[dict]:
    """Approved scenes only, in gallery order, with masters that exist on disk."""
    if manifests is None:
        manifests = gallery.load_manifests()
    records: list[dict] = []
    for scene in manifests:
        if scene.get("approval_status") != "Approved":
            continue
        images: list[dict] = []
        for field, label in MASTER_FIELDS:
            path = scene.get(field) or ""
            if not exists(path):
                continue
            images.append(
                {
                    "format": label,
                    "path": path,
                    "loc": absolute_asset_url(path),
                }
            )
        if not images:
            continue
        city = str(scene.get("city") or "").strip()
        country = str(scene.get("country") or "").strip()
        title = str(scene.get("caption") or "").strip()
        caption = str(scene.get("alt_text") or "").strip()
        records.append(
            {
                "entry_id": scene["entry_id"],
                "loc": page_url(scene["entry_id"]),
                "caption": caption,
                "title": title,
                "geo_location": f"{city}, {country}" if city and country else city or country,
                "images": images,
            }
        )
    return records


def render_sitemap(records: list[dict]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for record in records:
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_text(record['loc'])}</loc>")
        for image in record["images"]:
            lines.append("    <image:image>")
            lines.append(f"      <image:loc>{xml_text(image['loc'])}</image:loc>")
            lines.append(f"      <image:caption>{xml_text(record['caption'])}</image:caption>")
            lines.append(f"      <image:geo_location>{xml_text(record['geo_location'])}</image:geo_location>")
            lines.append(f"      <image:title>{xml_text(record['title'])}</image:title>")
            lines.append("    </image:image>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    return "\n".join(lines)


def format_counts(records: list[dict]) -> dict[str, int]:
    counts = {"16:9": 0, "4:5": 0, "9:16": 0}
    for record in records:
        for image in record["images"]:
            counts[image["format"]] += 1
    return counts


def skipped_candidates() -> list[str]:
    skipped: list[str] = []
    for path in sorted((ROOT / "manifests").glob("CH-*.json")):
        scene = json.loads(path.read_text(encoding="utf-8"))
        if scene.get("approval_status") != "Approved":
            skipped.append(scene.get("entry_id") or path.stem)
    return skipped


def write_sitemap(path: Path = SITEMAP_PATH) -> dict:
    records = approved_image_records()
    xml = render_sitemap(records)
    path.write_text(xml, encoding="utf-8")
    counts = format_counts(records)
    return {
        "scenes": len(records),
        "images": sum(counts.values()),
        "formats": counts,
        "skipped_candidates": skipped_candidates(),
        "path": str(path),
    }


def main() -> None:
    stats = write_sitemap()
    counts = stats["formats"]
    print(
        f"wrote {stats['path']} scenes={stats['scenes']} images={stats['images']} "
        f"16:9={counts['16:9']} 4:5={counts['4:5']} 9:16={counts['9:16']}"
    )
    print("skipped candidates: " + ", ".join(stats["skipped_candidates"]))


if __name__ == "__main__":
    main()

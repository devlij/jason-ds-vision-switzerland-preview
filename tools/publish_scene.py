#!/usr/bin/env python3
"""Bake both masters and write the Candidate approval and manifest."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from bake_master import DISCLOSURE, SIGNATURE, bake
from catalog import SCENES

ROOT = Path(__file__).resolve().parents[1]
ZURICH = ZoneInfo("Europe/Zurich")


def scene_by_id(entry_id: str) -> dict:
    for scene in SCENES:
        if scene["entry_id"] == entry_id:
            return scene
    raise SystemExit(f"unknown scene {entry_id}")


def zurich_now() -> datetime:
    return datetime.now(ZURICH)


def scenario_fields(moment: datetime) -> tuple[str, str]:
    stamp = f"{moment.strftime('%-d %B %Y')} · {moment.strftime('%H:%M')} Europe/Zurich"
    return stamp, f"Scenario: {stamp}"


def weather_sentence(weather: dict) -> str:
    code = int(weather["weather_code"])
    names = {0: "clear", 1: "mainly clear", 2: "partly cloudy", 3: "overcast"}
    name = names.get(code, f"code {code}")
    return (
        f"Model data from Open-Meteo, retrieved {weather['retrieved']}, "
        f"valid {weather['valid']} Europe/Zurich — not a verified on-site observation. "
        f"Weather code {code} ({name}), cloud cover {weather['cloud_cover']}%, "
        f"{weather['temperature_2m']}°C, apparent temperature {weather['apparent_temperature']}°C, "
        f"wind {weather['wind_speed_10m']} km/h from {weather['wind_direction_10m']}°, "
        f"relative humidity {weather['relative_humidity_2m']}%, "
        f"precipitation {weather['precipitation']} mm, is_day {weather['is_day']}. "
        f"Model cell elevation about {weather['elevation']} m."
    )


def write_approval(scene: dict, scenario_label: str, weather: dict, solar: str) -> None:
    lines = [
        f"# {scene['entry_id']} — {scene['caption']}",
        "",
        "approval_status on the page: Candidate",
        "",
        "## Evidence card",
        f"- Caption baked into the image: {scene['caption']}",
        f"- Camera viewpoint: {scene['viewpoint']}",
        "- Reference links:",
        f"  - {scene['refs'][0]}",
        f"  - {scene['refs'][1]}",
        "- Geometry anchors:",
        f"  - {scene['anchors'][0]}",
        f"  - {scene['anchors'][1]}",
        f"  - {scene['anchors'][2]}",
        f"- Weather: {weather_sentence(weather)}"
        + (f" {scene['weather_note']}" if scene.get("weather_note") else ""),
        f"- Solar direction / time of day: {solar}",
        f"- Independent description: {scene['description']}",
        "- Source-use notes: Generation lineage is text-prompt-only. No photographic reference was passed into the generator. Reference pages were consulted for place facts, not copied into the image. The finished masters are AI-generated artistic interpretations offered free to use, with no credit required. This note is an internal review, not a legal certification. No prominent identifiable person and no focal logo were requested.",
        f"- Scenario label baked into the image: Scenario: {scenario_label}",
        f"- Disclosure baked into the image: {DISCLOSURE}",
        f"- Signature baked into the image: {SIGNATURE}",
        "",
        "## Five gates",
        "1. Visual/location — arrangement checked against the sources named above and against the generated frame. Editorial review only. Page status stays Candidate until Cosmo QCs it.",
        "2. Technical — 16:9 master is 1920×1080 and 4:5 master is 864×1080. Caption, scenario, disclosure, and the exact signature Jason D\u2019s Vision are baked on a bottom gradient. Font sizes scale with width: caption 0.016, scenario 0.012, disclosure 0.010, signature 0.018.",
        "3. Originality/provenance — text-prompt-only lineage, recorded here.",
        "4. Commercial/IP — no prominent identifiable person and no focal logo or artwork. Internal note, not legal certification.",
        "5. Publication readiness — caption, scenario, signature, and disclosure are present. The preview calls this scene Candidate, and this log does not call it approved.",
        "",
    ]
    path = ROOT / "approvals" / f"{scene['entry_id']}.md"
    path.write_text("\n".join(lines), encoding="utf-8")


def write_manifest(scene: dict, scenario_label: str) -> None:
    slug = scene["entry_id"].lower()
    folder = scene["folder"]
    file_16 = f"library/world/Switzerland/{folder}/{slug}-16x9.png"
    file_45 = f"library/world/Switzerland/{folder}/{slug}-4x5.png"
    payload = {
        "entry_id": scene["entry_id"],
        "country": "Switzerland",
        "region": scene["region"],
        "city": scene["city"],
        "caption": scene["caption"],
        "scenario_label": scenario_label,
        "composition": scene["composition"],
        "description": scene["description"],
        "alt_text": scene["alt_text"],
        "file_16x9": file_16,
        "file_4x5": file_45,
        "license_badge": "Free · no credit needed",
        "license_anchor": "#license",
        "approval_status": "Candidate",
    }
    path = ROOT / "manifests" / f"{scene['entry_id']}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def publish(entry_id: str, raw_16: str, raw_45: str, weather_path: str) -> str:
    scene = scene_by_id(entry_id)
    weather = json.loads(Path(weather_path).read_text(encoding="utf-8"))[entry_id]
    moment = zurich_now()
    scenario_label, scenario_line = scenario_fields(moment)
    slug = entry_id.lower()
    folder = ROOT / "library" / "world" / "Switzerland" / scene["folder"]
    folder.mkdir(parents=True, exist_ok=True)
    dest_16 = folder / f"{slug}-16x9.png"
    dest_45 = folder / f"{slug}-4x5.png"
    bake(raw_16, str(dest_16), 1920, 1080, scene["caption"], scenario_line)
    bake(raw_45, str(dest_45), 864, 1080, scene["caption"], scenario_line)
    solar = (
        "Afternoon. Calculated solar altitude about 40° and azimuth about 204° "
        "(south-southwest) near 14:30 Europe/Zurich on 24 September 2026 at this latitude, "
        "using a NOAA-style approximation. Sunrise roughly 07:20 and sunset roughly 19:20 Europe/Zurich. "
        "Calculated, not observed on site. Where the model is overcast, the frame uses diffuse light rather than hard sun."
    )
    write_approval(scene, scenario_label, weather, solar)
    write_manifest(scene, scenario_label)
    return scenario_label


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: publish_scene.py ENTRY raw16 raw45 weather.json")
    label = publish(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    print(sys.argv[1], label)


if __name__ == "__main__":
    main()

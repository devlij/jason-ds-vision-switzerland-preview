#!/usr/bin/env python3
"""Bake both masters and write the Candidate approval and manifest."""

from __future__ import annotations

import json
import math
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


WMO_NAMES = {
    0: "clear",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    95: "thunderstorm",
}


def weather_sentence(weather: dict) -> str:
    code = int(weather["weather_code"])
    name = WMO_NAMES.get(code, f"code {code}")
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


def _decl_eqtime(moment: datetime) -> tuple[float, float]:
    utc = moment.astimezone(ZoneInfo("UTC"))
    day = utc.timetuple().tm_yday
    hour = utc.hour + utc.minute / 60 + utc.second / 3600
    gamma = 2 * math.pi / 365 * (day - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )
    return decl, eqtime


def solar_position(lat: float, lon: float, moment: datetime) -> tuple[float, float]:
    decl, eqtime = _decl_eqtime(moment)
    tz_hours = moment.utcoffset().total_seconds() / 3600
    local_minutes = moment.hour * 60 + moment.minute + moment.second / 60
    tst = local_minutes + eqtime + 4 * lon - 60 * tz_hours
    ha = math.radians(tst / 4 - 180)
    latr = math.radians(lat)
    cosz = math.sin(latr) * math.sin(decl) + math.cos(latr) * math.cos(decl) * math.cos(ha)
    cosz = max(-1.0, min(1.0, cosz))
    altitude = 90 - math.degrees(math.acos(cosz))
    azimuth = math.degrees(
        math.atan2(
            -math.sin(ha),
            math.tan(decl) * math.cos(latr) - math.sin(latr) * math.cos(ha),
        )
    )
    return altitude, azimuth % 360


def compass_16(azimuth: float) -> str:
    names = [
        "north",
        "north-northeast",
        "northeast",
        "east-northeast",
        "east",
        "east-southeast",
        "southeast",
        "south-southeast",
        "south",
        "south-southwest",
        "southwest",
        "west-southwest",
        "west",
        "west-northwest",
        "northwest",
        "north-northwest",
    ]
    return names[int((azimuth + 11.25) // 22.5) % 16]


def sun_times(lat: float, lon: float, moment: datetime) -> tuple[str, str]:
    decl, eqtime = _decl_eqtime(moment)
    latr = math.radians(lat)
    arg = max(-1.0, min(1.0, -math.tan(latr) * math.tan(decl)))
    hour_angle = math.degrees(math.acos(arg))
    tz_hours = moment.utcoffset().total_seconds() / 3600
    noon = 720 - eqtime - 4 * lon + 60 * tz_hours

    def fmt(minutes: float) -> str:
        minutes = minutes % (24 * 60)
        hour = int(minutes // 60)
        minute = int(round(minutes % 60))
        if minute == 60:
            hour = (hour + 1) % 24
            minute = 0
        return f"{hour:02d}:{minute:02d}"

    return fmt(noon - hour_angle * 4), fmt(noon + hour_angle * 4)


def solar_sentence(scene: dict, moment: datetime) -> str:
    altitude, azimuth = solar_position(float(scene["lat"]), float(scene["lon"]), moment)
    rise, sett = sun_times(float(scene["lat"]), float(scene["lon"]), moment)
    if altitude <= 0:
        when = "Night"
    elif moment.hour < 12:
        when = "Morning"
    else:
        when = "Afternoon"
    return (
        f"{when}. Calculated solar altitude about {altitude:.0f}° and azimuth about {azimuth:.0f}° "
        f"({compass_16(azimuth)}) at {moment.strftime('%H:%M')} Europe/Zurich on {moment.strftime('%-d %B %Y')} "
        f"at this latitude, using a NOAA-style approximation. Sunrise roughly {rise} and sunset roughly {sett} Europe/Zurich. "
        "Calculated, not observed on site. Where the model is overcast, the frame uses diffuse light rather than hard sun."
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
    write_approval(scene, scenario_label, weather, solar_sentence(scene, moment))
    write_manifest(scene, scenario_label)
    return scenario_label


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: publish_scene.py ENTRY raw16 raw45 weather.json")
    label = publish(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    print(sys.argv[1], label)


if __name__ == "__main__":
    main()

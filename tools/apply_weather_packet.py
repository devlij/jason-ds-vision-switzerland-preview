#!/usr/bin/env python3
"""Record a per-scene Open-Meteo retrieval and point the manifest at the new masters.

Leaves approval_status at Candidate. Does not write an approval.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WMO = {
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
    95: "thunderstorm",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def weather_bullet(row: dict) -> str:
    code = int(row["weather_code"])
    name = WMO.get(code, f"code {code}")
    return (
        f"- Weather: Model data from Open-Meteo, retrieved {row['retrieved_utc']} "
        f"({row['retrieved_zurich']} Europe/Zurich), HTTP Date {row['http_date']}, "
        f"valid {row['valid']} Europe/Zurich — not a verified on-site observation. "
        f"Separate HTTP GET for {row['latitude']}, {row['longitude']}. "
        f"The model-valid hour is {row['model_valid_hour']} Europe/Zurich. "
        f"The cited model time is the {row['valid'][-5:]} step (interval 3600 seconds). "
        f"Scenario 24 September 2026 {row['scenario_minute']} Europe/Zurich falls inside that model-valid hour. "
        f"Weather code {code} ({name}), cloud cover {row['cloud_cover']}%, "
        f"{row['temperature_2m']}°C, apparent temperature {row['apparent_temperature']}°C, "
        f"wind {row['wind_speed_10m']} km/h from {row['wind_direction_10m']}°, "
        f"relative humidity {row['relative_humidity_2m']}%, "
        f"precipitation {row['precipitation']} mm, is_day {row['is_day']}. "
        f"Model cell elevation about {row['elevation']} m."
    )


def patch_markdown(path: Path, row: dict) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "approval_status on the page: Approved",
        "approval_status on the page: Candidate",
        1,
    )
    if "approval_status on the page: Candidate" not in text.split("## Evidence", 1)[0]:
        text = re.sub(
            r"approval_status on the page: .*",
            "approval_status on the page: Candidate",
            text,
            count=1,
        )
    bullet = weather_bullet(row)
    text2, n = re.subn(r"- Weather: .*", bullet, text, count=1)
    if n != 1:
        raise SystemExit(f"{path} weather bullet not replaced")
    text = text2
    if int(row["weather_code"]) != 3:
        text = text.replace("fully overcast", "partly cloudy")
        text = text.replace("is overcast", "is partly cloudy")
    text = text.replace(
        "2. Technical — 16:9 master is 1920×1080 and 4:5 master is 864×1080. Caption, scenario, disclosure, and the exact signature Jason D’s Vision are baked on a bottom gradient. Font sizes scale with width: caption 0.016, scenario 0.012, disclosure 0.010, signature 0.018.",
        "2. Technical — 16:9 master is 1920×1270, 4:5 master is 864×1270, and 9:16 master is 1080×2110. The photograph is pure. A 190px #0e0e12 bar with a 2px hairline holds the caption, scenario, disclosure, curly-apostrophe Jason D’s Vision, and Allura Jason A. Devlin.",
    )
    text = text.replace(
        "- Signature baked into the image: Jason D’s Vision",
        "- Signature baked into the image: Jason D’s Vision (curly apostrophe) and Jason A. Devlin in Allura, both inside the label bar",
    )
    note = (
        "\n## Weather rework 2026-09-27\n"
        "Builder rework. One Open-Meteo archive HTTP GET for this scene, not a shared request. "
        f"HTTP Date {row['http_date']}. Retrieved {row['retrieved_utc']}. "
        f"Model-valid hour {row['model_valid_hour']} Europe/Zurich contains scenario minute {row['scenario_minute']}. "
        "Masters were re-rendered to match that model hour and the label-bar finish. "
        "approval_status is Candidate. This note is not an approval.\n"
    )
    if "## Weather rework 2026-09-27" not in text:
        text = text.rstrip() + note
    path.write_text(text, encoding="utf-8")


def patch_manifest(path: Path, row: dict) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    entry_id = data["entry_id"].lower()
    folder = Path(data["file_16x9"]).parent
    files = {
        "file_16x9": folder / f"{entry_id}-16x9.png",
        "file_4x5": folder / f"{entry_id}-4x5.png",
        "file_9x16": folder / f"{entry_id}-9x16.png",
    }
    for key, rel in files.items():
        full = ROOT / rel
        if not full.is_file():
            raise SystemExit(f"missing master {full}")
        data[key] = str(rel)
        data["sha256_" + key.split("_", 1)[1]] = sha256(full)
    if int(row["weather_code"]) != 3:
        description = data.get("description") or ""
        description = description.replace("fully overcast", "partly cloudy")
        description = description.replace("is overcast", "is partly cloudy")
        data["description"] = description
    data["approval_status"] = "Candidate"
    data["qc_status"] = "Candidate · weather rework 2026-09-27 · not approved"
    data.pop("approved_at", None)
    code = int(row["weather_code"])
    name = WMO.get(code, f"code {code}")
    data["approval_basis"] = (
        f"Builder weather rework 2026-09-27 for {data['entry_id']}. "
        f"Own Open-Meteo archive GET, HTTP Date {row['http_date']}, retrieved {row['retrieved_utc']}, "
        f"valid {row['valid']} Europe/Zurich, model-valid hour {row['model_valid_hour']}, "
        f"scenario 24 September 2026 · {row['scenario_minute']} Europe/Zurich inside that hour. "
        f"Weather code {code} ({name}), cloud {row['cloud_cover']}%, {row['temperature_2m']}°C, "
        f"is_day {row['is_day']}. Masters re-rendered at 1920×1270, 864×1270, and 1080×2110 "
        "with a 190px #0e0e12 label bar. Status Candidate. Not an approval."
    )
    data["open_meteo"] = {
        "retrieved_utc": row["retrieved_utc"],
        "http_date": row["http_date"],
        "valid": row["valid"],
        "model_valid_hour": row["model_valid_hour"],
        "scenario_minute": row["scenario_minute"],
        "weather_code": row["weather_code"],
        "cloud_cover": row["cloud_cover"],
        "temperature_2m": row["temperature_2m"],
        "apparent_temperature": row["apparent_temperature"],
        "wind_speed_10m": row["wind_speed_10m"],
        "wind_direction_10m": row["wind_direction_10m"],
        "relative_humidity_2m": row["relative_humidity_2m"],
        "precipitation": row["precipitation"],
        "is_day": row["is_day"],
        "elevation": row["elevation"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
    }
    notes = data.setdefault("qc_notes", [])
    notes.append(
        {
            "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "by": "builder",
            "note": data["approval_basis"],
        }
    )
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_weather_packet.py LEDGER.json CH-01-001,CH-01-002,...")
    ledger = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    by_id = {row["entry_id"]: row for row in ledger["scenes"]}
    ids = sys.argv[2].split(",")
    for entry_id in ids:
        row = by_id[entry_id]
        patch_markdown(ROOT / "approvals" / f"{entry_id}.md", row)
        patch_manifest(ROOT / "manifests" / f"{entry_id}.json", row)
        print("packet", entry_id, row["retrieved_utc"])


if __name__ == "__main__":
    main()

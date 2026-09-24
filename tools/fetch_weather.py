#!/usr/bin/env python3
"""Fetch Open-Meteo current model data for catalog scenes."""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import SCENES


def fetch(entry_ids: list[str]) -> dict:
    wanted = []
    for entry_id in entry_ids:
        for scene in SCENES:
            if scene["entry_id"] == entry_id:
                wanted.append(scene)
                break
        else:
            raise SystemExit(f"unknown scene {entry_id}")
    lats = ",".join(str(scene["lat"]) for scene in wanted)
    lons = ",".join(str(scene["lon"]) for scene in wanted)
    url = (
        "https://api.open-meteo.com/v1/forecast?latitude="
        + lats
        + "&longitude="
        + lons
        + "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
        + "weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,is_day"
        + "&timezone=Europe%2FZurich"
    )
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = json.load(response)
    items = payload if isinstance(payload, list) else [payload]
    if len(items) != len(wanted):
        raise SystemExit(f"Open-Meteo returned {len(items)} rows for {len(wanted)} scenes")
    retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {}
    for scene, item in zip(wanted, items):
        current = item["current"]
        out[scene["entry_id"]] = {
            "retrieved": retrieved,
            "valid": current["time"],
            "weather_code": current["weather_code"],
            "cloud_cover": current["cloud_cover"],
            "temperature_2m": current["temperature_2m"],
            "apparent_temperature": current["apparent_temperature"],
            "wind_speed_10m": current["wind_speed_10m"],
            "wind_direction_10m": current["wind_direction_10m"],
            "relative_humidity_2m": current["relative_humidity_2m"],
            "precipitation": current["precipitation"],
            "is_day": current["is_day"],
            "elevation": item.get("elevation"),
        }
    return out


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: fetch_weather.py OUT.json CH-01-017 [CH-01-018 ...]")
    payload = fetch(sys.argv[2:])
    Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for entry_id, row in payload.items():
        print(
            entry_id,
            row["valid"],
            "code",
            row["weather_code"],
            "cloud",
            row["cloud_cover"],
            "t",
            row["temperature_2m"],
            "elev",
            row["elevation"],
        )


if __name__ == "__main__":
    main()

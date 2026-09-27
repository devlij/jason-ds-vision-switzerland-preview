#!/usr/bin/env python3
"""One Open-Meteo archive HTTP GET per scene.

Reads the Date header. Retries until that UTC second is unique against
timestamps already stored and against every retrieval timestamp already
written in approvals/. Does not batch coordinates into one request.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import SCENES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOURLY = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
    "weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,is_day"
)
TS_RE = re.compile(r"retrieved (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)")
HOUR_RE = re.compile(r"Scenario: \d{1,2} \w+ \d{4} · (\d{2}):(\d{2}) Europe/Zurich")
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def existing_timestamps() -> set[str]:
    found: set[str] = set()
    for path in (ROOT / "approvals").glob("CH-*.md"):
        found.update(TS_RE.findall(path.read_text(encoding="utf-8")))
    return found


def scenario_hour(entry_id: str) -> tuple[int, int]:
    text = (ROOT / "approvals" / f"{entry_id}.md").read_text(encoding="utf-8")
    match = HOUR_RE.search(text)
    if not match:
        raise SystemExit(f"{entry_id} has no scenario hour")
    return int(match.group(1)), int(match.group(2))


def scene_by_id(entry_id: str) -> dict:
    for scene in SCENES:
        if scene["entry_id"] == entry_id:
            return scene
    raise SystemExit(f"unknown scene {entry_id}")


def fetch_one(scene: dict, hour: int, minute: int, used: set[str]) -> dict:
    url = (
        f"{ARCHIVE}?latitude={scene['lat']}&longitude={scene['lon']}"
        f"&start_date=2026-09-24&end_date=2026-09-24&hourly={HOURLY}"
        "&timezone=Europe%2FZurich"
    )
    for attempt in range(8):
        request = urllib.request.Request(url, headers={"User-Agent": "jason-ds-vision-ch-weather/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                http_date = response.headers.get("Date") or ""
                status = response.status
                body = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                time.sleep(3 + attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2 + attempt)
            continue
        if not http_date:
            time.sleep(1.1)
            continue
        stamp = parsedate_to_datetime(http_date).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if stamp in used:
            time.sleep(1.15)
            continue
        payload = json.loads(body)
        times = payload["hourly"]["time"]
        key = f"2026-09-24T{hour:02d}:00"
        if key not in times:
            raise SystemExit(f"{scene['entry_id']} missing model hour {key}")
        index = times.index(key)
        hourly = payload["hourly"]
        used.add(stamp)
        zurich = parsedate_to_datetime(http_date).astimezone(
            __import__("zoneinfo").ZoneInfo("Europe/Zurich")
        )
        return {
            "entry_id": scene["entry_id"],
            "latitude": scene["lat"],
            "longitude": scene["lon"],
            "http_status": status,
            "http_date": http_date,
            "retrieved_utc": stamp,
            "retrieved_zurich": zurich.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "valid": key,
            "model_valid_hour": f"{hour:02d}:00–{hour:02d}:59",
            "scenario_minute": f"{hour:02d}:{minute:02d}",
            "scenario_inside_hour": True,
            "weather_code": hourly["weather_code"][index],
            "cloud_cover": hourly["cloud_cover"][index],
            "temperature_2m": hourly["temperature_2m"][index],
            "apparent_temperature": hourly["apparent_temperature"][index],
            "wind_speed_10m": hourly["wind_speed_10m"][index],
            "wind_direction_10m": hourly["wind_direction_10m"][index],
            "relative_humidity_2m": hourly["relative_humidity_2m"][index],
            "precipitation": hourly["precipitation"][index],
            "is_day": hourly["is_day"][index],
            "elevation": payload.get("elevation"),
            "url": url,
        }
    raise SystemExit(f"{scene['entry_id']} could not obtain a unique HTTP Date")


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: fetch_archive_weather.py OUT.json CH-01-001 [CH-01-002 ...]")
    out = Path(sys.argv[1])
    used = existing_timestamps()
    if out.exists():
        prior = json.loads(out.read_text(encoding="utf-8"))
        for row in prior.get("scenes", []):
            used.add(row["retrieved_utc"])
    else:
        prior = {"scenes": []}
    by_id = {row["entry_id"]: row for row in prior["scenes"]}
    for entry_id in sys.argv[2:]:
        if entry_id in by_id:
            print("skip", entry_id, by_id[entry_id]["retrieved_utc"])
            continue
        scene = scene_by_id(entry_id)
        hour, minute = scenario_hour(entry_id)
        row = fetch_one(scene, hour, minute, used)
        by_id[entry_id] = row
        print(
            entry_id,
            row["retrieved_utc"],
            "valid",
            row["valid"],
            "code",
            row["weather_code"],
            "cloud",
            row["cloud_cover"],
            "t",
            row["temperature_2m"],
            "day",
            row["is_day"],
        )
        out.write_text(
            json.dumps({"scenes": [by_id[k] for k in sorted(by_id)]}, indent=2) + "\n",
            encoding="utf-8",
        )
    stamps = [row["retrieved_utc"] for row in by_id.values()]
    if len(stamps) != len(set(stamps)):
        raise SystemExit("ledger contains a duplicate timestamp")


if __name__ == "__main__":
    main()

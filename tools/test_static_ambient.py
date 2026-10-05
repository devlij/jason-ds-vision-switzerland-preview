#!/usr/bin/env python3
"""Selector and fail-once streak rules for static-ambient packs."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import build_index as gallery  # noqa: E402
import static_ambient as ambient  # noqa: E402


def _scene(entry_id: str, hour: int, source: str = "day") -> dict:
    return {
        "entry_id": entry_id,
        "scenario_label": f"24 September 2026 · {hour:02d}:00 Europe/Zurich",
        "caption": entry_id,
        "file_4x5": f"library/{entry_id.lower()}-4x5.png",
        "daylight_variant": {"files": {"4x5": f"library/{entry_id.lower()}-daylight-4x5.png"}},
        "_source": source,
    }


def test_day_tag_wins_over_night_hour_and_night_tag_stays_out() -> None:
    scenes = [
        _scene("CH-01-001", 14),
        _scene("CH-01-002", 19),
        _scene("CH-01-003", 14),
        _scene("CH-01-004", 5),
        _scene("CH-01-005", 12),
        _scene("CH-01-006", 20),
    ]
    tags = {
        "CH-01-001": "day",
        "CH-01-002": "day",
        "CH-01-003": "night",
        "CH-01-004": "day",
    }
    chosen = [
        scene["entry_id"]
        for scene in ambient.select_candidates(scenes, tags, set(), exists=lambda entry_id: False)
    ]
    assert chosen == ["CH-01-001", "CH-01-002", "CH-01-004", "CH-01-005"]
    assert ambient.is_daylight_scene(scenes[1], "day") is True
    assert ambient.is_daylight_scene(scenes[2], "night") is False
    assert ambient.is_daylight_scene(scenes[4], None) is True
    assert ambient.is_daylight_scene(scenes[5], None) is False


def test_lowest_ids_skip_existing_clips_and_holds() -> None:
    scenes = [_scene(f"CH-01-{i:03d}", 14) for i in range(1, 6)]
    tags = {scene["entry_id"]: "day" for scene in scenes}
    assert ambient.motion_rel("CH-01-001") == "assets/ch-01-001-motion-10s-4x5.mp4"
    chosen = [
        scene["entry_id"]
        for scene in ambient.select_candidates(
            scenes,
            tags,
            {"CH-01-001"},
            exists=lambda entry_id: entry_id == "CH-01-002",
        )
    ]
    assert chosen == ["CH-01-003", "CH-01-004", "CH-01-005"]


def test_three_different_holds_stop_without_a_fourth_attempt() -> None:
    scenes = [_scene(f"CH-01-{i:03d}", 14) for i in range(1, 6)]
    calls: list[str] = []

    def produce(scene: dict):
        calls.append(scene["entry_id"])
        if scene["entry_id"] == "CH-01-002":
            return "pass", "right"
        return "hold", "qc"

    # hold, pass, hold, hold, hold would continue; this sequence is
    # hold, hold, hold on the first three and must not call the fourth.
    def all_hold(scene: dict):
        calls.append(scene["entry_id"])
        return "hold", "qc"

    calls.clear()
    outcome = ambient.consume(scenes, all_hold, limit=12)
    assert outcome["stopped_early"] is True
    assert calls == ["CH-01-001", "CH-01-002", "CH-01-003"]

    calls.clear()
    mixed = ambient.consume(scenes, produce, limit=12)
    assert mixed["stopped_early"] is True
    assert calls == ["CH-01-001", "CH-01-002", "CH-01-003", "CH-01-004", "CH-01-005"]
    assert [row["qc"] for row in mixed["attempted"]] == ["hold", "pass", "hold", "hold", "hold"]


def test_initial_streak_stops_on_the_next_hold() -> None:
    scenes = [_scene(f"CH-01-{i:03d}", 14) for i in range(1, 4)]
    calls: list[str] = []

    def all_hold(scene: dict):
        calls.append(scene["entry_id"])
        return "hold", "qc"

    outcome = ambient.consume(scenes, all_hold, limit=12, initial_streak=2)
    assert outcome["stopped_early"] is True
    assert outcome["streak"] == 3
    assert calls == ["CH-01-001"]


def test_a_pass_resets_the_streak() -> None:
    scenes = [_scene(f"CH-01-{i:03d}", 12) for i in range(1, 5)]

    def produce(scene: dict):
        if scene["entry_id"] in {"CH-01-001", "CH-01-003"}:
            return "hold", "qc"
        return "pass", "left"

    outcome = ambient.consume(scenes, produce, limit=12)
    assert outcome["stopped_early"] is False
    assert len(outcome["attempted"]) == 4


def test_motion_button_is_published_only_when_the_clip_exists() -> None:
    def exists(path: str) -> bool:
        if path.startswith("assets/") and path.endswith("-motion-10s-4x5.mp4"):
            return path.endswith("ch-01-001-motion-10s-4x5.mp4")
        return gallery.master_exists(path)

    scenes = gallery.publishable_scenes(gallery.load_manifests(), exists)
    by_id = {scene["entry_id"]: scene for scene in scenes}
    assert by_id["CH-01-001"]["file_motion_4x5"] == "assets/ch-01-001-motion-10s-4x5.mp4"
    assert "file_motion_4x5" not in by_id["CH-01-013"]
    html = gallery.render_index([by_id["CH-01-001"]], {})
    assert 'class="motion"' in html
    assert "assets/ch-01-001-motion-10s-4x5.mp4" in html
    rendered = gallery.render_index([by_id["CH-01-013"]], {})
    payload = rendered.split("const SCENES = ", 1)[1].split(";\n", 1)[0]
    assert "file_motion_4x5" not in payload


def main() -> None:
    test_day_tag_wins_over_night_hour_and_night_tag_stays_out()
    test_lowest_ids_skip_existing_clips_and_holds()
    test_three_different_holds_stop_without_a_fourth_attempt()
    test_initial_streak_stops_on_the_next_hold()
    test_a_pass_resets_the_streak()
    test_motion_button_is_published_only_when_the_clip_exists()
    print("static-ambient tests passed")


if __name__ == "__main__":
    main()

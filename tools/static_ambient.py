#!/usr/bin/env python3
"""Static-ambient Ken Burns clips from daylight 4:5 masters.

Night masters are never inputs. A scene is attempted once: a failed self-QC
is a HOLD, and three consecutive HOLDs on different scenes stop the pack.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "manifests"
TAGS = ROOT / "tools" / "phase1_tags.json"
ASSETS = ROOT / "assets"
EVIDENCE = ROOT / "evidence"
INDEX = ROOT / "index.html"

ENTRY_RE = re.compile(r"^CH-\d{2}-\d{3}$")
HOUR_RE = re.compile(r"(\d{1,2}):(\d{2})")

PHOTO_W, PHOTO_H = 864, 1080
CANVAS_H = 1270
BAR_H = 190
HAIRLINE = (228, 228, 234)  # #E4E4EA
BAR = (14, 14, 18)  # #0E0E12
FPS = 30
FRAMES = 300
DURATION = 10.0

# Locked from pilot encodes of CH-01-001, CH-01-004, and CH-01-007.
# A still encode sits near 1.3 MAD; the gentlest real push measured 6.2.
START_MAD_MAX = 3.0
ENDS_MAD_MIN = 3.5
ENDS_MAD_MAX = 45.0
ADJ_MAD_MAX = 1.5

PANS = ("right", "left", "down", "up")
METHOD = "static-ambient"


def motion_rel(entry_id: str) -> str:
    return f"assets/{entry_id.lower()}-motion-10s-4x5.mp4"


def evidence_path(entry_id: str) -> Path:
    return EVIDENCE / f"{entry_id}-motion.json"


def scenario_hour(scene: dict) -> int | None:
    match = HOUR_RE.search(str(scene.get("scenario_label") or ""))
    if not match:
        return None
    return int(match.group(1))


def is_night_hour(hour: int | None) -> bool:
    return hour is not None and (hour >= 18 or hour < 6)


def is_daylight_scene(scene: dict, tag: str | None) -> bool:
    """Daylight only. A night tag or a night-hour scenario excludes the scene."""
    if tag == "night":
        return False
    hour = scenario_hour(scene)
    if is_night_hour(hour):
        return False
    if tag == "day":
        return True
    # No phase-1 tag: trust a daytime scenario hour, and nothing else.
    return hour is not None


def daylight_source(scene: dict) -> str:
    variant = scene.get("daylight_variant")
    files = variant.get("files") if isinstance(variant, dict) else None
    if not isinstance(files, dict):
        return ""
    return str(files.get("4x5") or "")


def _entry_num(entry_id: str) -> int:
    return int(entry_id.rsplit("-", 1)[-1])


def load_scenes() -> list[dict]:
    found: list[dict] = []
    for path in sorted(MANIFESTS.glob("CH-*.json")):
        scene = json.loads(path.read_text(encoding="utf-8"))
        entry_id = scene.get("entry_id") or ""
        if ENTRY_RE.fullmatch(entry_id):
            found.append(scene)
    found.sort(key=lambda scene: _entry_num(scene["entry_id"]))
    return found


def load_tags() -> dict[str, str]:
    if not TAGS.exists():
        return {}
    raw = json.loads(TAGS.read_text(encoding="utf-8"))
    return {entry_id: str((row or {}).get("daynight") or "") for entry_id, row in raw.items()}


def held_ids() -> set[str]:
    held: set[str] = set()
    if not EVIDENCE.exists():
        return held
    for path in EVIDENCE.glob("CH-*-motion.json"):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if row.get("qc") == "hold" and row.get("entry_id"):
            held.add(row["entry_id"])
    return held


def select_candidates(
    scenes: list[dict],
    tags: dict[str, str],
    held: set[str] | None = None,
    exists=None,
) -> list[dict]:
    """Lowest daylight ids that still have no motion clip and are not on HOLD."""
    held = held or set()
    if exists is None:
        exists = lambda entry_id: (ROOT / motion_rel(entry_id)).is_file()
    chosen: list[dict] = []
    for scene in scenes:
        entry_id = scene["entry_id"]
        if entry_id in held or exists(entry_id):
            continue
        if not is_daylight_scene(scene, tags.get(entry_id) or None):
            continue
        chosen.append(scene)
    return chosen


def consume(candidates: list[dict], produce, limit: int = 12) -> dict:
    """One attempt per scene. Three different HOLDs in a row stop the pack."""
    attempted: list[dict] = []
    streak = 0
    stopped = False
    for scene in candidates[:limit]:
        qc, reason = produce(scene)
        attempted.append({"entry_id": scene["entry_id"], "qc": qc, "reason": reason})
        if qc == "hold":
            streak += 1
            if streak >= 3:
                stopped = True
                break
        else:
            streak = 0
    return {"attempted": attempted, "stopped_early": stopped}


def _png_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as handle:
        if handle.read(8) != b"\x89PNG\r\n\x1a\n":
            return None
        handle.read(4)
        if handle.read(4) != b"IHDR":
            return None
        width = int.from_bytes(handle.read(4), "big")
        height = int.from_bytes(handle.read(4), "big")
        return width, height


def _column(path: Path, x: int) -> bytes:
    raw = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path),
            "-vf", f"crop=1:ih:{x}:0",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ]
    )
    return raw


def _pixel(column: bytes, y: int) -> tuple[int, int, int]:
    i = y * 3
    return column[i], column[i + 1], column[i + 2]


def geometry_failure(path: Path) -> str | None:
    size = _png_size(path)
    if size != (PHOTO_W, CANVAS_H):
        return f"4:5 master is {size}, expected {PHOTO_W}x{CANVAS_H}"
    for x in (2, 430):
        column = _column(path, x)
        if len(column) < CANVAS_H * 3:
            return f"could not read column x={x}"
        if _pixel(column, PHOTO_H) != HAIRLINE or _pixel(column, PHOTO_H + 1) != HAIRLINE:
            return f"hairline missing at y={PHOTO_H} x={x}"
        if _pixel(column, CANVAS_H - 1) != BAR:
            return f"label bar missing at bottom x={x}"
    return None


def _pan_expr(entry_id: str) -> tuple[str, str, str]:
    ease = "(0.5-0.5*cos(PI*on/299))"
    pan = PANS[(_entry_num(entry_id) - 1) % 4]
    x = "(iw-iw/zoom)*0.5"
    y = "(ih-ih/zoom)*0.5"
    if pan == "right":
        x = f"(iw-iw/zoom)*(0.5+0.18*{ease})"
    elif pan == "left":
        x = f"(iw-iw/zoom)*(0.5-0.18*{ease})"
    elif pan == "down":
        y = f"(ih-ih/zoom)*(0.5+0.18*{ease})"
    else:
        y = f"(ih-ih/zoom)*(0.5-0.18*{ease})"
    return pan, x, y


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _encode(crop: Path, dest: Path, entry_id: str) -> str:
    _pan, x_expr, y_expr = _pan_expr(entry_id)
    vf = (
        "scale=3456:4320:flags=lanczos,"
        "zoompan="
        f"z='1+0.07*(0.5-0.5*cos(PI*on/299))':"
        f"x='{x_expr}':y='{y_expr}':d={FRAMES}:s={PHOTO_W}x{PHOTO_H}:fps={FPS}"
    )
    _run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(crop),
            "-vf", vf,
            "-frames:v", str(FRAMES),
            "-r", str(FPS),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            "-crf", "20",
            "-an",
            "-movflags", "+faststart",
            str(dest),
        ]
    )
    return _pan


def _probe(path: Path) -> dict:
    raw = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_streams", "-show_format",
            "-of", "json", str(path),
        ]
    )
    return json.loads(raw)


def _frame_png(video: Path, n: int, dest: Path) -> None:
    _run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(video),
            "-vf", f"select=eq(n\\,{n})",
            "-frames:v", "1", str(dest),
        ]
    )


def _mad(a: bytes, b: bytes) -> float:
    n = min(len(a), len(b)) // 3
    if n == 0:
        return 999.0
    total = 0
    for i in range(n):
        total += abs(a[i * 3] - b[i * 3])
        total += abs(a[i * 3 + 1] - b[i * 3 + 1])
        total += abs(a[i * 3 + 2] - b[i * 3 + 2])
    return total / (n * 3)


def _scaled_rgb(path: Path) -> bytes:
    return subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path),
            "-vf", "scale=96:120",
            "-frames:v", "1",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ]
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _qc_video(video: Path, crop: Path) -> tuple[str | None, dict]:
    probe = _probe(video)
    streams = probe.get("streams") or []
    video_streams = [row for row in streams if row.get("codec_type") == "video"]
    audio_streams = [row for row in streams if row.get("codec_type") == "audio"]
    metrics: dict = {}
    if len(video_streams) != 1 or audio_streams:
        return "expected one video stream and no audio", metrics
    stream = video_streams[0]
    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    frames = int(stream.get("nb_frames") or 0)
    duration = float(stream.get("duration") or probe.get("format", {}).get("duration") or 0)
    metrics.update(width=width, height=height, frames=frames, duration_s=duration)
    if (width, height) != (PHOTO_W, PHOTO_H):
        return f"output is {width}x{height}", metrics
    if stream.get("codec_name") != "h264" or stream.get("pix_fmt") != "yuv420p":
        return "output is not h264 yuv420p", metrics
    if frames != FRAMES or abs(duration - DURATION) > 0.001:
        return f"duration {duration} frames {frames}", metrics
    with tempfile.TemporaryDirectory(prefix="kb-qc-") as tmp:
        folder = Path(tmp)
        first, second, last = folder / "f0.png", folder / "f1.png", folder / "f299.png"
        _frame_png(video, 0, first)
        _frame_png(video, 1, second)
        _frame_png(video, FRAMES - 1, last)
        start_mad = _mad(_scaled_rgb(first), _scaled_rgb(crop))
        adjacent = _mad(_scaled_rgb(first), _scaled_rgb(second))
        ends = _mad(_scaled_rgb(first), _scaled_rgb(last))
    metrics.update(start_vs_source_mad=round(start_mad, 3), adjacent_mad=round(adjacent, 3), ends_mad=round(ends, 3))
    if start_mad > START_MAD_MAX:
        return f"opening frame does not match the cropped photo ({start_mad:.2f})", metrics
    if not (ENDS_MAD_MIN <= ends <= ENDS_MAD_MAX):
        return f"Ken Burns delta {ends:.2f} outside {ENDS_MAD_MIN}-{ENDS_MAD_MAX}", metrics
    if adjacent > ADJ_MAD_MAX:
        return f"opening step is not smooth ({adjacent:.2f})", metrics
    return None, metrics


def attempt(scene: dict) -> tuple[str, str]:
    """Encode once. Any QC miss HOLDs this scene and leaves no mp4."""
    entry_id = scene["entry_id"]
    source_rel = daylight_source(scene)
    night_rel = str(scene.get("file_4x5") or "")
    if not source_rel.endswith("-daylight-4x5.png"):
        _write_hold(scene, "daylight 4:5 master missing")
        return "hold", "daylight 4:5 master missing"
    if source_rel == night_rel:
        _write_hold(scene, "source is the night master")
        return "hold", "source is the night master"
    source = ROOT / source_rel
    if not source.is_file():
        _write_hold(scene, "daylight 4:5 file missing")
        return "hold", "daylight 4:5 file missing"
    problem = geometry_failure(source)
    if problem:
        _write_hold(scene, problem)
        return "hold", problem
    dest = ROOT / motion_rel(entry_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    pan = ""
    try:
        with tempfile.TemporaryDirectory(prefix="kb-") as tmp:
            crop = Path(tmp) / "crop.png"
            _run(
                [
                    "ffmpeg", "-y", "-v", "error", "-i", str(source),
                    "-vf", f"crop={PHOTO_W}:{PHOTO_H}:0:0",
                    "-frames:v", "1", str(crop),
                ]
            )
            pan = _encode(crop, dest, entry_id)
            problem, metrics = _qc_video(dest, crop)
    except subprocess.CalledProcessError as exc:
        dest.unlink(missing_ok=True)
        reason = "ffmpeg failed"
        _write_hold(scene, reason, detail=(exc.stderr or b"").decode("utf-8", "replace")[-400:])
        return "hold", reason
    if problem:
        dest.unlink(missing_ok=True)
        _write_hold(scene, problem, metrics=metrics)
        return "hold", problem
    record = {
        "entry_id": entry_id,
        "caption": scene.get("caption") or "",
        "method": METHOD,
        "daylight": True,
        "night_master_used": False,
        "source": source_rel,
        "night_master": night_rel,
        "crop": {"x": 0, "y": 0, "width": PHOTO_W, "height": PHOTO_H, "label_bar_px": BAR_H},
        "output": motion_rel(entry_id),
        "duration_s": DURATION,
        "width": PHOTO_W,
        "height": PHOTO_H,
        "fps": FPS,
        "frames": FRAMES,
        "ken_burns": {
            "zoom": "1.00 to 1.07, cosine ease",
            "pan": pan,
            "tool": "ffmpeg zoompan",
        },
        "qc": "pass",
        "sha256": _sha256(dest),
        "metrics": metrics,
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    evidence_path(entry_id).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return "pass", pan


def _write_hold(scene: dict, reason: str, metrics: dict | None = None, detail: str = "") -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    record = {
        "entry_id": scene["entry_id"],
        "caption": scene.get("caption") or "",
        "method": METHOD,
        "daylight": True,
        "night_master_used": False,
        "source": daylight_source(scene),
        "qc": "hold",
        "qc_reason": reason,
    }
    if metrics:
        record["metrics"] = metrics
    if detail:
        record["detail"] = detail
    evidence_path(scene["entry_id"]).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def wire_motion_buttons(passed: list[str]) -> None:
    """Add file_motion_4x5 on the live gallery records that have a clip."""
    if not INDEX.exists() or not passed:
        return
    text = INDEX.read_text(encoding="utf-8")
    for entry_id in passed:
        rel = motion_rel(entry_id)
        field = f'"file_motion_4x5": "{rel}"'
        if field in text:
            continue
        needle = f'{entry_id.lower()}-daylight-4x5.png",'
        insert = needle + f'\n    {field},'
        if text.count(needle) != 1:
            raise SystemExit(f"could not wire {entry_id}: daylight path count {text.count(needle)}")
        text = text.replace(needle, insert, 1)
    INDEX.write_text(text, encoding="utf-8")


def remaining_daylight(scenes: list[dict], tags: dict[str, str]) -> list[str]:
    missing: list[str] = []
    for scene in scenes:
        entry_id = scene["entry_id"]
        if not is_daylight_scene(scene, tags.get(entry_id) or None):
            continue
        if not (ROOT / motion_rel(entry_id)).is_file():
            missing.append(entry_id)
    return missing


def run_pack(limit: int = 12) -> dict:
    scenes = load_scenes()
    tags = load_tags()
    candidates = select_candidates(scenes, tags, held_ids())
    outcome = consume(candidates, attempt, limit)
    passed = [row["entry_id"] for row in outcome["attempted"] if row["qc"] == "pass"]
    holds = [row for row in outcome["attempted"] if row["qc"] == "hold"]
    wire_motion_buttons(passed)
    missing = remaining_daylight(scenes, tags)
    summary = {
        "pack": 1,
        "method": METHOD,
        "limit": limit,
        "passed": passed,
        "holds": holds,
        "stopped_early": outcome["stopped_early"],
        "remaining_daylight_missing": missing,
        "remaining_count": len(missing),
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "static-ambient-pack-1.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    summary = run_pack(12)
    print(json.dumps({k: summary[k] for k in ("passed", "holds", "stopped_early", "remaining_count")}, indent=2))


if __name__ == "__main__":
    main()

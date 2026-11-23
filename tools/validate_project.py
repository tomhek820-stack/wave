#!/usr/bin/env python3
"""Deterministic preflight checks for a ZORO VIDEO DIRECTOR PRO project.

Usage:
  python tools/validate_project.py --project-dir path/to/project
  python tools/validate_project.py --project-dir path/to/project --skip-inputs

Expected project layout:
  input/audio/voiceover.wav
  input/text/voiceover.txt
  input/text/video_content.md
  project/scene_plan.json
  project/assets_manifest.json
  output/final_video.mp4
  output/subtitles.srt (or .ass)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def parse_srt(path: Path, errors: list[str]) -> int:
    raw = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\r?\n\s*\r?\n", raw.strip())
    valid = 0
    timestamp = re.compile(
        r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+"
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
    )
    for number, block in enumerate(blocks, 1):
        lines = block.splitlines()
        if len(lines) < 3 or not lines[0].strip().isdigit():
            fail(errors, f"SRT block {number}: missing numeric index or subtitle text")
            continue
        match = timestamp.match(lines[1].strip())
        if not match:
            fail(errors, f"SRT block {number}: invalid timestamp line")
            continue
        values = [int(x) for x in match.groups()]
        start_ms = ((values[0] * 60 + values[1]) * 60 + values[2]) * 1000 + values[3]
        end_ms = ((values[4] * 60 + values[5]) * 60 + values[6]) * 1000 + values[7]
        if end_ms <= start_ms:
            fail(errors, f"SRT block {number}: end must be after start")
            continue
        if not any(line.strip() for line in lines[2:]):
            fail(errors, f"SRT block {number}: empty subtitle")
            continue
        valid += 1
    return valid


def check_ffprobe(audio: Path, errors: list[str]) -> None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        print("INFO: ffprobe unavailable; audio metadata check skipped (NOT RUN).")
        return
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        fail(errors, f"ffprobe could not read audio: {result.stderr.strip()}")
        return
    try:
        duration = float(result.stdout.strip())
        if duration <= 0:
            fail(errors, "Audio duration is not positive.")
        else:
            print(f"PASS: audio readable; duration={duration:.3f}s")
    except ValueError:
        fail(errors, "ffprobe returned an invalid audio duration.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True, type=Path)
    parser.add_argument("--skip-inputs", action="store_true")
    parser.add_argument("--check-final-output", action="store_true")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    errors: list[str] = []

    if not root.is_dir():
        print(f"FAIL: project directory does not exist: {root}")
        return 2

    required_inputs = [
        root / "input/audio/voiceover.wav",
        root / "input/text/voiceover.txt",
        root / "input/text/video_content.md",
    ]
    if not args.skip_inputs:
        for path in required_inputs:
            if not path.is_file() or path.stat().st_size == 0:
                fail(errors, f"Missing or empty required input: {path.relative_to(root)}")
            else:
                print(f"PASS: input exists: {path.relative_to(root)}")
        audio = required_inputs[0]
        if audio.is_file():
            check_ffprobe(audio, errors)

    scene_file = root / "project/scene_plan.json"
    if not scene_file.is_file():
        fail(errors, "Missing project/scene_plan.json")
    else:
        try:
            plan: dict[str, Any] = json.loads(scene_file.read_text(encoding="utf-8"))
            if plan.get("schema_version") != "1.0.0":
                fail(errors, "scene_plan.json: schema_version must be 1.0.0")
            scenes = plan.get("scenes")
            if not isinstance(scenes, list) or not scenes:
                fail(errors, "scene_plan.json: scenes must be a non-empty array")
            else:
                previous_start = -1.0
                ids: set[str] = set()
                for index, scene in enumerate(scenes, 1):
                    prefix = f"scene {index}"
                    scene_id = scene.get("scene_id")
                    if not isinstance(scene_id, str) or not scene_id:
                        fail(errors, f"{prefix}: missing scene_id")
                    elif scene_id in ids:
                        fail(errors, f"{prefix}: duplicate scene_id {scene_id}")
                    else:
                        ids.add(scene_id)
                    try:
                        start = float(scene["start_seconds"])
                        end = float(scene["end_seconds"])
                        if start < 0 or end <= start:
                            fail(errors, f"{prefix}: invalid time range")
                        if start < previous_start:
                            fail(errors, f"{prefix}: scenes are not ordered by start time")
                        previous_start = start
                    except (KeyError, TypeError, ValueError):
                        fail(errors, f"{prefix}: missing/invalid start_seconds or end_seconds")
                    for field in ("voiceover_exact", "narrative_beat", "visual_purpose"):
                        if not isinstance(scene.get(field), str) or not scene[field].strip():
                            fail(errors, f"{prefix}: missing {field}")
                if not errors:
                    print(f"PASS: scene plan parsed; {len(scenes)} ordered scenes")
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            fail(errors, f"scene_plan.json is invalid: {exc}")

    manifest = root / "project/assets_manifest.json"
    if not manifest.is_file():
        print("WARN: project/assets_manifest.json not found; asset provenance not checked.")
    else:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            assets = data.get("assets", [])
            if not isinstance(assets, list):
                fail(errors, "assets_manifest.json: assets must be an array")
            else:
                for item in assets:
                    asset_path = item.get("path")
                    if not asset_path:
                        fail(errors, "assets_manifest.json: asset missing path")
                    elif not (root / asset_path).is_file():
                        fail(errors, f"Manifest asset file missing: {asset_path}")
                if not errors:
                    print(f"PASS: asset manifest parsed; {len(assets)} assets")
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            fail(errors, f"assets_manifest.json is invalid: {exc}")

    subtitle_candidates = [root / "output/subtitles.srt", root / "output/subtitles.ass"]
    subtitle = next((p for p in subtitle_candidates if p.is_file()), None)
    if subtitle and subtitle.suffix.lower() == ".srt":
        count = parse_srt(subtitle, errors)
        if count:
            print(f"PASS: SRT structure valid; {count} subtitle blocks")
    elif subtitle:
        print("INFO: ASS subtitle file exists; detailed ASS parsing is not implemented.")
    else:
        print("WARN: no subtitles file found; subtitle check not passed.")

    if args.check_final_output:
        final_video = root / "output/final_video.mp4"
        if not final_video.is_file() or final_video.stat().st_size == 0:
            fail(errors, "Missing or empty output/final_video.mp4")
        else:
            print(f"PASS: final video file exists ({final_video.stat().st_size} bytes)")
            ffprobe = shutil.which("ffprobe")
            if ffprobe:
                result = subprocess.run(
                    [ffprobe, "-v", "error", "-show_entries",
                     "format=duration:stream=codec_type,width,height,avg_frame_rate",
                     "-of", "json", str(final_video)],
                    capture_output=True, text=True, check=False,
                )
                if result.returncode != 0:
                    fail(errors, "Final video failed ffprobe decoding.")
                else:
                    print("PASS: ffprobe inspected final video streams.")
            else:
                print("INFO: ffprobe unavailable; final media decode check NOT RUN.")

    if errors:
        print("\nVALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("\nVALIDATION: PASS for checks executed. Review all WARN/INFO lines; NOT RUN is not PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

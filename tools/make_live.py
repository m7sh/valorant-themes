#!/usr/bin/env python3
"""
Render an 8-second seamless live wallpaper per agent from its signature still.

Output: themes/valorant-<slug>/backgrounds/9-<slug>-live.mp4
(16:9, 2560x1440, 24 fps, silent H.264 loop; the still stays the default
background because it sorts first.)

Usage:
    python3 tools/make_live.py             # all agents
    python3 tools/make_live.py --only jett # one agent
    python3 tools/make_live.py --crf 30    # smaller files
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
WORK = Path("/tmp/opencode/live")

WIDTH, HEIGHT = 2560, 1440
FPS = 24
SECONDS = 8
CRF = 29


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def glow(agent: dict, colour: str, radius: int, tag: str) -> Path:
    p = WORK / f"{agent['slug']}-{tag}.png"
    run([
        "magick", "-size", f"{radius * 2}x{radius * 2}",
        f"radial-gradient:{colour}88-{colour}00", str(p),
    ])
    return p


def live_wallpaper(agent: dict, crf: int) -> Path:
    slug = agent["slug"]
    theme = THEMES / agent["theme"]
    still = sorted((theme / "backgrounds").glob("0-*.webp"))[0]
    dst = theme / "backgrounds" / f"9-{slug}-live.mp4"

    g1 = glow(agent, agent["accent"], 1000, "g1")
    g2 = glow(agent, agent["accent2"], 1200, "g2")

    frames = FPS * SECONDS
    source_w = int(WIDTH * 1.1)
    source_h = int(HEIGHT * 1.1)

    zoom = f"1.06+0.035*cos(2*PI*on/{frames})"
    pan = f"30*sin(2*PI*on/{frames})"
    period = SECONDS

    graph = (
        f"[0:v]scale={source_w}:{source_h}:flags=lanczos,"
        f"zoompan=z='{zoom}':x='(iw-iw/zoom)/2+{pan}':"
        f"y='(ih-ih/zoom)/2':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}[bg];"
        f"[1:v]format=rgba,colorchannelmixer=aa=0.24[g1];"
        f"[2:v]format=rgba,colorchannelmixer=aa=0.14[g2];"
        f"[bg][g1]overlay=x='(W-w)/2+110*sin(2*PI*t/{period})':"
        f"y='(H-h)/2+80*cos(2*PI*t/{period})':eval=frame[t1];"
        f"[t1][g2]overlay=x='(W-w)/2-90*sin(2*PI*t/{period}+1.7)':"
        f"y='(H-h)/2-70*cos(2*PI*t/{period}+1.7)':eval=frame,"
        f"format=yuv420p[v]"
    )

    run([
        "ffmpeg", "-v", "error", "-y", "-i", str(still), "-i", str(g1), "-i", str(g2),
        "-filter_complex", graph, "-map", "[v]", "-frames:v", str(frames),
        "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(dst),
    ])
    return dst


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="render one agent slug")
    parser.add_argument("--crf", type=int, default=CRF)
    args = parser.parse_args()

    WORK.mkdir(parents=True, exist_ok=True)
    agents = json.loads((ROOT / "agents.json").read_text())
    for agent in agents:
        if args.only and agent["slug"] != args.only:
            continue
        path = live_wallpaper(agent, args.crf)
        print(f"  {agent['slug']:<12} {path.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()

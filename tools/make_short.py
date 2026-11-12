#!/usr/bin/env python3
"""
Render a 9:16 short-form promo video for the theme bundle.

Reads agents.json, builds one 2160x3840 still per agent (4K wallpaper crop +
text card), then cuts a ~15 s silent vertical video with ffmpeg:
intro -> 30 agents (0.43 s each) -> outro.

Requires ImageMagick 7 (`magick`) and ffmpeg.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"
PORTRAITS = ASSETS / "portraits"
WORK = Path("/tmp/opencode/short")

BEBAS = FONTS / "BebasNeue-Regular.ttf"
RAJ_B = FONTS / "Rajdhani-Bold.ttf"
RAJ_SB = FONTS / "Rajdhani-SemiBold.ttf"
RAJ_M = FONTS / "Rajdhani-Medium.ttf"

W, H = 2160, 3840          # render size; encoded down to 1080x1920
FPS = 30
AGENT_FRAMES = 13          # 0.43 s per agent
INTRO_FRAMES = 21          # 0.7 s
OUTRO_FRAMES = 36          # 1.2 s

INK_WHITE = "#FFFFFF"
INK_SOFT = "#F2F6F8"
INK_MUTED = "#8C99A4"
INK_DIM = "#7F8C96"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def out(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def size(p: Path) -> tuple[int, int]:
    w, h = out(["magick", "identify", "-format", "%w %h", str(p)]).split()
    return int(w), int(h)


def label(text: str, font: Path, pointsize: int, fill: str, tag: str,
          kerning: int = 0) -> Path:
    p = WORK / f"t-{tag}.png"
    cmd = ["magick", "-background", "none", "-fill", fill,
           "-font", str(font), "-pointsize", str(pointsize)]
    if kerning:
        cmd += ["-kerning", str(kerning)]
    cmd += [f"label:{text}", "-trim", "+repage", str(p)]
    run(cmd)
    return p


def scaled_label(text: str, font: Path, pointsize: int, fill: str, tag: str,
                 max_width: int) -> Path:
    p = label(text, font, pointsize, fill, tag)
    w, _ = size(p)
    if w > max_width:
        run(["magick", str(p), "-filter", "Lanczos", "-resize", f"{max_width}x",
             "+repage", str(p)])
    return p


def centered(p: Path, y: int, canvas: int = W) -> list[str]:
    w, _ = size(p)
    return [str(p), "-geometry", f"+{(canvas - w) // 2}+{y}",
            "-compose", "over", "-composite"]


def scrim() -> Path:
    """Top and bottom darkening so type reads over any render."""
    p = WORK / "scrim.png"
    run([
        "magick", "-size", f"{W}x{H}", "xc:none",
        "(", "-size", f"{W}x{H}", "xc:none", "-fill", "#05060A",
        "-draw", f"rectangle 0,0 {W},780", "-blur", "0x120",
        "-channel", "A", "-evaluate", "multiply", "0.55", "+channel", ")",
        "-compose", "over", "-composite",
        "(", "-size", f"{W}x{H}", "xc:none", "-fill", "#05060A",
        "-draw", f"rectangle 0,2180 {W},{H}", "-blur", "0x150",
        "-channel", "A", "-evaluate", "multiply", "0.92", "+channel", ")",
        "-compose", "over", "-composite",
        str(p),
    ])
    return p


def glow(accent: str, accent2: str, tag: str) -> Path:
    p = WORK / f"glow-{tag}.png"
    run([
        "magick", "-size", "1080x1920", f"xc:#080912",
        "(", "-size", "1080x1920", f"radial-gradient:{accent}66-{accent}00", ")",
        "-compose", "over", "-composite",
        "(", "-size", "1080x1920", f"radial-gradient:{accent2}44-{accent2}00", ")",
        "-compose", "over", "-composite",
        "-resize", f"{W}x{H}!", str(p),
    ])
    return p


def portrait_center(slug: str) -> float:
    """Horizontal centre of the agent render in the 3840x2160 wallpaper."""
    portrait = PORTRAITS / f"{slug}.png"
    tw, th = out(["magick", str(portrait), "-trim", "-format", "%w %h", "info:"]).split()
    drawn_w = int(tw) * 2040 / int(th)
    return 3780 - drawn_w / 2


def agent_still(agent: dict, index: int, total: int) -> Path:
    slug = agent["slug"]
    accent = agent["accent"]
    accent2 = agent["accent2"]
    dst = WORK / f"still-{slug}.png"

    wall = sorted((ROOT / "themes" / agent["theme"] / "backgrounds").glob("0-*.webp"))[0]
    bgw = int(out(["magick", "identify", "-format", "%w", str(wall)]))
    scale = H / 2160
    crop_w = int(round(bgw * scale))
    cx = portrait_center(slug) * (crop_w / 3840)
    x = max(0, min(int(cx - W / 2), crop_w - W))

    name_img = scaled_label(agent["name"].upper(), BEBAS, 440, INK_WHITE, f"{slug}-name", 1880)
    _, nh = size(name_img)
    role_img = label(f"{agent['role'].upper()}   //   {agent['origin']}",
                     RAJ_B, 82, accent, f"{slug}-role")
    _, rh = size(role_img)

    name_y = 2140
    role_y = name_y + nh + 44
    rule_y = role_y + rh + 46

    eyebrow = label(f"// VALORANT PROTOCOL   ·   AGENT {agent['number']}",
                    RAJ_SB, 56, accent, f"{slug}-eyebrow")
    sig_label = label("SIGNATURE", RAJ_SB, 50, INK_MUTED, f"{slug}-sig-l")
    sig_img = scaled_label(agent["signature"].upper(), BEBAS, 180, INK_SOFT,
                           f"{slug}-sig", 1880)
    ult_label = label("ULTIMATE", RAJ_SB, 50, INK_MUTED, f"{slug}-ult-l")
    ult_img = scaled_label(agent["ultimate"].upper(), BEBAS, 140, accent2,
                           f"{slug}-ult", 1880)

    progress = int(W * (index + 1) / total)
    cmd = [
        "magick", str(wall), "-auto-orient", "-filter", "Lanczos",
        "-resize", f"{crop_w}x{H}!", "-crop", f"{W}x{H}+{x}+0", "+repage",
        str(WORK / "scrim.png"), "-compose", "over", "-composite",
        "-gravity", "northwest", "-compose", "over",
        "-fill", "#2A2F38", "-draw", f"rectangle 0,{H - 52} {W},{H - 36}",
        "-fill", accent, "-draw", f"rectangle 0,{H - 52} {progress},{H - 36}",
    ]
    cmd += centered(eyebrow, 180)
    cmd += centered(name_img, name_y)
    cmd += centered(role_img, role_y)
    cmd += ["-fill", accent, "-draw",
            f"rectangle {(W - 460) // 2},{rule_y} {(W + 460) // 2},{rule_y + 10}"]
    cmd += centered(sig_label, 2960)
    cmd += centered(sig_img, 3030)
    cmd += centered(ult_label, 3250)
    cmd += centered(ult_img, 3310)
    cmd += [str(dst)]
    run(cmd)
    return dst


def intro_still() -> Path:
    dst = WORK / "intro.png"
    bg = glow("#A97BFF", "#4FD1C5", "intro")
    cmd = ["magick", str(bg)]
    cmd += ["-gravity", "northwest", "-compose", "over"]
    cmd += centered(label("V A L O R A N T", RAJ_B, 96, "#A97BFF", "in-1", 10), 1210)
    cmd += centered(label("30 AGENT", BEBAS, 340, INK_WHITE, "in-2"), 1390)
    cmd += centered(label("THEMES", BEBAS, 340, INK_WHITE, "in-3"), 1690)
    cmd += centered(label("FOR OMARCHY", RAJ_M, 104, "#C9D2DA", "in-4"), 2110)
    cmd += centered(label("ONE REPO   ·   EVERY AGENT", RAJ_SB, 56, INK_MUTED, "in-5"), 2280)
    cmd += ["-fill", "#A97BFF", "-draw",
            f"rectangle {(W - 560) // 2},2020 {(W + 560) // 2},2028"]
    cmd += [str(dst)]
    run(cmd)
    return dst


def outro_still() -> Path:
    dst = WORK / "outro.png"
    bg = glow("#4FD1C5", "#A97BFF", "outro")
    cmd = ["magick", str(bg), "-gravity", "northwest", "-compose", "over"]
    cmd += centered(label("AVAILABLE NOW", RAJ_SB, 60, "#4FD1C5", "out-1"), 1170)
    cmd += centered(scaled_label("github.com/m7sh/valorant-themes", RAJ_B, 76,
                                 INK_WHITE, "out-2", 1900), 1290)
    cmd += centered(label("./install.sh", BEBAS, 300, "#4FD1C5", "out-3"), 1490)
    cmd += centered(label("ONE COMMAND   ·   ALL 30 AGENTS", RAJ_SB, 66,
                          "#C9D2DA", "out-4"), 1960)
    cmd += centered(label("VALORANT  //  AGENT THEMES", RAJ_SB, 46, INK_DIM, "out-5"), 3300)
    cmd += [str(dst)]
    run(cmd)
    return dst


def encode(still: Path, frames: int, clip: Path, accent: str) -> None:
    zoom_w = f"{W}-8*n"
    zoom_h = f"{H}-15*n"
    vf = (
        f"crop=w='{zoom_w}':h='{zoom_h}':x='(iw-ow)/2':y='(ih-oh)/2',"
        f"scale=1080:1920:flags=lanczos,setsar=1,"
        f"fade=t=in:st=0:d=0.07:color=0x{accent.lstrip('#')}"
    )
    run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(still),
        "-vf", vf, "-frames:v", str(frames), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-pix_fmt", "yuv420p", "-an", str(clip),
    ])


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    for stale in WORK.glob("*.png"):
        stale.unlink()
    for f in WORK.glob("clip-*.mp4"):
        f.unlink()

    agents = json.loads((ROOT / "agents.json").read_text())
    total = len(agents)

    scrim()

    clips: list[Path] = []

    intro = intro_still()
    clip = WORK / "clip-000-intro.mp4"
    encode(intro, INTRO_FRAMES, clip, "#0A0A12")
    clips.append(clip)

    for i, agent in enumerate(agents):
        still = agent_still(agent, i, total)
        clip = WORK / f"clip-{i + 1:03d}-{agent['slug']}.mp4"
        encode(still, AGENT_FRAMES, clip, agent["accent"])
        clips.append(clip)
        print(f"  {i + 1:02d}/{total} {agent['name']}")

    outro = outro_still()
    clip = WORK / "clip-999-outro.mp4"
    encode(outro, OUTRO_FRAMES, clip, "#0A0A12")
    clips.append(clip)

    listing = WORK / "concat.txt"
    listing.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")
    dst = ASSETS / "valorant-themes-short.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", "-movflags", "+faststart", str(dst),
    ])

    poster = ASSETS / "valorant-themes-short-poster.jpg"
    run(["ffmpeg", "-y", "-i", str(dst), "-vf", "select=eq(n\\,120)",
         "-frames:v", "1", "-q:v", "2", str(poster)])

    secs = (INTRO_FRAMES + total * AGENT_FRAMES + OUTRO_FRAMES) / FPS
    print(f"wrote {dst} ({secs:.1f}s, {dst.stat().st_size / 1e6:.1f} MB)")
    print(f"wrote {poster}")


if __name__ == "__main__":
    main()

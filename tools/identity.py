#!/usr/bin/env python3
"""
Add the per-theme identity assets Omarchy looks for:

    preview.png          theme switcher card (1365x768)
    shell.toml           bar accent + Hyprland border gradient
    unlock.png           Plymouth boot logo (800x188)
    preview-unlock.png   Plymouth picker mock (1920x1080)

Run after tools/build.py so the signature wallpapers already exist.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
FONTS = ROOT / "assets" / "fonts"
WORK = Path("/tmp/opencode/identity")

BEBAS = FONTS / "BebasNeue-Regular.ttf"
RAJ_B = FONTS / "Rajdhani-Bold.ttf"
RAJ_SB = FONTS / "Rajdhani-SemiBold.ttf"
RAJ_M = FONTS / "Rajdhani-Medium.ttf"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def out(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def size(p: Path) -> tuple[int, int]:
    w, h = out(["magick", "identify", "-format", "%w %h", str(p)]).split()
    return int(w), int(h)


def label(text: str, font: Path, pointsize: int, fill: str, tag: str) -> Path:
    p = WORK / f"l-{tag}.png"
    run(["magick", "-background", "none", "-fill", fill, "-font", str(font),
         "-pointsize", str(pointsize), f"label:{text}", "-trim", "+repage", str(p)])
    return p


def fit_label(text: str, font: Path, pointsize: int, fill: str, tag: str,
              max_width: int) -> Path:
    p = label(text, font, pointsize, fill, tag)
    w, _ = size(p)
    if w > max_width:
        run(["magick", str(p), "-filter", "Lanczos", "-resize", f"{max_width}x",
             "+repage", str(p)])
    return p


def colors(theme: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in (THEMES / theme / "colors.toml").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition("=")
            data[key.strip()] = value.strip().strip('"')
    return data


def preview_card(agent: dict, pal: dict[str, str]) -> Path:
    """Theme switcher card: agent render right, type + palette left."""
    slug = agent["slug"]
    theme = THEMES / agent["theme"]
    portrait = ROOT / "assets" / "portraits" / f"{slug}.png"
    dst = theme / "preview.jpg"
    (theme / "preview.png").unlink(missing_ok=True)

    accent, accent2 = agent["accent"], agent["accent2"]
    bg = pal["background"]
    fg = pal.get("foreground", "#E8ECF2")
    muted = pal.get("muted", "#7F8C96")
    lighter = pal.get("lighter_background", "#1B2228")

    name = fit_label(agent["name"].upper(), BEBAS, 104, "#FFFFFF", f"{slug}-name", 600)
    role = label(f"{agent['role'].upper()}   //   {agent['origin']}", RAJ_B, 22,
                 accent, f"{slug}-role")
    eyebrow = label(f"// AGENT {agent['number']}", RAJ_SB, 18, accent, f"{slug}-eb")
    footer = label("VALORANT  //  AGENT THEMES", RAJ_M, 15, muted, f"{slug}-ft")

    _, nh = size(name)

    chips = [accent, accent2, fg, muted, lighter]
    chip_cmd: list[str] = []
    x = 56
    for colour in chips:
        chip_cmd += ["-fill", colour, "-stroke", "#3A4048", "-strokewidth", "1",
                     "-draw", f"rectangle {x},596 {x + 30},626"]
        x += 40

    cmd = [
        "magick", "-size", "1365x768", f"xc:{bg}",
        "(", "-size", "1365x768", f"radial-gradient:{accent}66-{accent}00", ")",
        "-compose", "over", "-composite",
        "-gravity", "northeast", "-compose", "over",
        "(", str(portrait), "-filter", "Lanczos", "-trim", "+repage",
        "-resize", "x690", ")",
        "-geometry", "+40+58", "-composite",
        "-gravity", "northwest",
        "(", "-size", "1365x768", "xc:none", "-fill", bg,
        "-draw", "rectangle 0,0 560,768", "-blur", "0x34", ")",
        "-compose", "over", "-composite",
        str(eyebrow), "-geometry", "+56+52", "-composite",
        str(name), "-geometry", "+50+186", "-composite",
        str(role), "-geometry", f"+56+{186 + nh + 12}", "-composite",
        *chip_cmd,
        str(footer), "-geometry", "+56+722", "-composite",
        "-strip", "-quality", "92", str(dst),
    ]
    run(cmd)
    return dst


def shell_toml(agent: dict, pal: dict[str, str]) -> Path:
    theme = THEMES / agent["theme"]
    dst = theme / "shell.toml"
    accent, accent2 = agent["accent"], agent["accent2"]
    bg = pal["background"]
    fg = pal.get("foreground", "#E8ECF2")
    dst.write_text(
        "# Agent-accent overrides; Omarchy fills every other key from colors.toml.\n"
        "\n"
        "[bar]\n"
        f'active           = "{accent}"\n'
        f'background       = "{bg}"\n'
        "background-alpha = 0.94\n"
        f'text             = "{fg}"\n'
        "\n"
        "[hyprland]\n"
        f'active-border            = "{accent} {accent2} 90deg"\n'
        f'active-border-foreground = "{fg}"\n'
        "\n"
        "[controls]\n"
        f'hover-cursor-border = "{accent}"\n'
        f'hover-cursor-color  = "{fg}"\n'
        f'focus-border        = "{accent}"\n'
        f'focus-color         = "{fg}"\n'
        f'selected-color      = "{fg}"\n'
        f'selected-border     = "{accent}"\n',
        encoding="utf-8",
    )
    return dst


def boot_logo(agent: dict, pal: dict[str, str]) -> Path:
    """800x188 transparent wordmark for the Plymouth boot splash."""
    theme = THEMES / agent["theme"]
    dst = theme / "unlock.png"
    accent = agent["accent"]
    fg = pal.get("foreground", "#E8ECF2")

    name = fit_label(agent["name"].upper(), BEBAS, 96, fg, f"{agent['slug']}-logo", 680)
    _, nh = size(name)
    caption = label("V A L O R A N T", RAJ_SB, 17, accent, f"{agent['slug']}-cap")

    # 800x188: name, accent rule, caption, vertically centred.
    rule_w = 260
    block = nh + 10 + 6 + 12 + 17
    top = (188 - block) // 2
    cmd = ["magick", "-size", "800x188", "xc:none",
           "-gravity", "northwest", "-compose", "over",
           str(name), "-geometry", f"+{(800 - size(name)[0]) // 2}+{top}",
           "-composite",
           "-fill", accent, "-draw",
           f"rectangle {(800 - rule_w) // 2},{top + nh + 10} "
           f"{(800 + rule_w) // 2},{top + nh + 16}",
           str(caption),
           "-geometry", f"+{(800 - size(caption)[0]) // 2}+{top + nh + 28}",
           "-composite", str(dst)]
    run(cmd)
    return dst


def boot_preview(agent: dict, pal: dict[str, str], logo: Path) -> Path:
    """1920x1080 mock of the boot/lock screen, used by the plymouth picker."""
    theme = THEMES / agent["theme"]
    dst = theme / "preview-unlock.png"
    accent, accent2 = agent["accent"], agent["accent2"]
    bg = pal["background"]
    muted = pal.get("muted", "#7F8C96")

    big = WORK / f"{agent['slug']}-logo-big.png"
    run(["magick", str(logo), "-resize", "1120x", "+repage", str(big)])
    _, lh = size(big)

    hint = label("PRESS  ENTER  TO  UNLOCK", RAJ_SB, 20, muted, f"{agent['slug']}-hint")
    cmd = [
        "magick", "-size", "1920x1080", f"xc:{bg}",
        "(", "-size", "1920x1080", f"radial-gradient:{accent}30-{accent2}00", ")",
        "-compose", "over", "-composite",
        "-gravity", "northwest", "-compose", "over",
        str(big), "-geometry", f"+{(1920 - size(big)[0]) // 2}+300", "-composite",
        "-fill", "none", "-stroke", "#3A4048", "-strokewidth", "2",
        "-draw", "roundrectangle 730,{0} 1190,{1} 30,30".format(300 + lh + 90, 300 + lh + 154),
        "-fill", accent, "-stroke", "none",
    ]
    for i in range(4):
        cx = 902 + i * 32
        cmd += ["-draw", f"circle {cx},{300 + lh + 122} {cx},{300 + lh + 128}"]
    cmd += [str(hint), "-geometry", f"+{(1920 - size(hint)[0]) // 2}+{300 + lh + 200}",
            "-composite", "-depth", "8", "-strip", str(dst)]
    run(cmd)
    return dst


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    agents = json.loads((ROOT / "agents.json").read_text())
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for agent in agents:
        if only and agent["slug"] != only:
            continue
        pal = colors(agent["theme"])
        preview_card(agent, pal)
        shell_toml(agent, pal)
        logo = boot_logo(agent, pal)
        boot_preview(agent, pal, logo)
        print(f"  identity {agent['slug']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Add the per-theme identity assets Omarchy looks for:

    preview.jpg          theme switcher card (1365x768)
    shell.toml           bar, borders, launcher, menu, notifications, lock
    unlock.png           Plymouth boot logo (800x188)
    preview-unlock.png   Plymouth picker mock (1920x1080)

Run after tools/build.py so colors.toml already exists.
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
    """Theme switcher card: agent render right, type + 10-swatch palette left."""
    slug = agent["slug"]
    theme = THEMES / agent["theme"]
    portrait = ROOT / "assets" / "portraits" / f"{slug}.png"
    dst = theme / "preview.jpg"
    (theme / "preview.png").unlink(missing_ok=True)

    light_mode = pal.get("mode", "dark") == "light"
    accent = pal["accent"]
    accent2 = pal.get("icon_mark", agent["accent2"])
    bg = pal["background"]
    fg = pal.get("foreground", "#E8ECF2")
    muted = pal.get("dark_foreground", pal.get("muted", "#7F8C96"))
    lighter = pal.get("lighter_background", "#1B2228")

    name = fit_label(agent["name"].upper(), BEBAS, 108, fg, f"{slug}-name", 580)
    role = label(f"{agent['role'].upper()}   //   {agent['origin']}", RAJ_B, 22,
                 accent2, f"{slug}-role")
    eyebrow = label(f"// AGENT {agent['number']}  ·  {pal.get('mode', 'dark').upper()}",
                    RAJ_SB, 18, accent, f"{slug}-eb")
    sig_txt = label(f"SIG: {agent['signature'].upper()}", RAJ_M, 16, muted, f"{slug}-sig")
    ult_txt = label(f"ULT: {agent['ultimate'].upper()}", RAJ_M, 16, accent2, f"{slug}-ult")
    footer = label("VALORANT  //  OMARCHY AGENT THEMES", RAJ_M, 15, muted, f"{slug}-ft")

    _, nh = size(name)
    _, rh = size(role)

    chips = [
        bg, lighter, accent, accent2, fg,
        pal["red"], pal["yellow"], pal["green"], pal["cyan"], pal["magenta"],
    ]
    stroke_col = "#B8C2CC" if light_mode else "#3A4048"
    chip_cmd: list[str] = []
    x = 56
    for i, colour in enumerate(chips):
        chip_cmd += [
            "-fill", colour, "-stroke", stroke_col, "-strokewidth", "1",
            "-draw", f"roundrectangle {x},592 {x + 36},628 4,4",
        ]
        x += 44 if i != 4 else 52

    a1 = "42" if light_mode else "66"
    a2 = "28" if light_mode else "40"
    rule_y = 178 + nh + 12 + rh + 16

    cmd = [
        "magick", "-size", "1365x768", f"xc:{bg}",
        "(", "-size", "1100x1100", f"radial-gradient:{accent}{a1}-{accent}00", ")",
        "-gravity", "northwest", "-geometry", "+360-180", "-compose", "over", "-composite",
        "(", "-size", "900x900", f"radial-gradient:{accent2}{a2}-{accent2}00", ")",
        "-gravity", "northwest", "-geometry", "-220+180", "-compose", "over", "-composite",
        "-gravity", "northeast", "-compose", "over",
        "(", str(portrait), "-filter", "Lanczos", "-trim", "+repage",
        "-resize", "x690", ")",
        "-geometry", "+40+58", "-composite",
        "-gravity", "northwest",
        "(", "-size", "1365x768", "xc:none", "-fill", bg,
        "-draw", "rectangle 0,0 520,768", "-blur", "0x38",
        "-channel", "A", "-evaluate", "multiply", "0.86", "+channel", ")",
        "-compose", "over", "-composite",
        str(eyebrow), "-geometry", "+56+52", "-composite",
        str(name), "-geometry", "+50+178", "-composite",
        str(role), "-geometry", f"+56+{178 + nh + 12}", "-composite",
        "-fill", accent, "-stroke", "none",
        "-draw", f"rectangle 56,{rule_y} 166,{rule_y + 3}",
        "-fill", accent2,
        "-draw", f"rectangle 172,{rule_y} 230,{rule_y + 3}",
        str(sig_txt), "-geometry", "+56+508", "-composite",
        str(ult_txt), "-geometry", "+56+534", "-composite",
        *chip_cmd,
        str(footer), "-geometry", "+56+722", "-composite",
        "-strip", "-quality", "92", str(dst),
    ]
    run(cmd)
    return dst


def shell_toml(agent: dict, pal: dict[str, str]) -> Path:
    theme = THEMES / agent["theme"]
    dst = theme / "shell.toml"
    light_mode = pal.get("mode", "dark") == "light"
    accent = pal["accent"]
    accent2 = pal.get("icon_mark", agent["accent2"])
    bg = pal["background"]
    darker_bg = pal.get("darker_background", bg)
    fg = pal.get("foreground", "#E8ECF2")
    muted = pal.get("muted", "#7F8C96")
    err = pal.get("red", "#F05A5A")
    placeholder = pal.get("dark_foreground", muted)

    role = agent["role"]
    bar_alpha = "0.96" if light_mode else ("0.92" if role == "Controller" else "0.95")
    scrim_alpha = "0.34" if light_mode else "0.58"
    border_w = "2" if role in ("Duelist", "Sentinel") else "2"
    sel_fill_alpha = "0.14" if light_mode else "0.16"
    grad = f"{accent} {accent2} 45deg"

    dst.write_text(
        "# Agent-tailored Omarchy shell surface tokens.\n"
        "\n"
        "[bar]\n"
        f'background       = "{bg}"\n'
        f"background-alpha = {bar_alpha}\n"
        f'text             = "{fg}"\n'
        f'active           = "{accent}"\n'
        "scale-with-font  = true\n"
        "size-horizontal  = 26\n"
        "size-vertical    = 28\n"
        "\n"
        "[hyprland]\n"
        f'active-border            = "{grad}"\n'
        f'active-border-foreground = "{fg}"\n'
        "\n"
        "[controls]\n"
        f'normal-color        = "{fg}"\n'
        "normal-fill-alpha   = 0.04\n"
        f'normal-border       = "{muted}"\n'
        "normal-border-width = 1\n"
        "normal-border-alpha = 0.45\n"
        "\n"
        f'hover-cursor-color        = "{fg}"\n'
        "hover-cursor-fill-alpha   = 0.10\n"
        f'hover-cursor-border       = "{accent}"\n'
        "hover-cursor-border-width = 1\n"
        "hover-cursor-border-alpha = 0.70\n"
        "\n"
        f'focus-color        = "{fg}"\n'
        "focus-fill-alpha   = 0.12\n"
        f'focus-border       = "{accent2}"\n'
        "focus-border-width = 1\n"
        "focus-border-alpha = 0.80\n"
        "\n"
        f'selected-color        = "{fg}"\n'
        "selected-fill-alpha   = 0.22\n"
        f'selected-border       = "{accent}"\n'
        "selected-border-width = 1\n"
        "selected-border-alpha = 1.0\n"
        "\n"
        "pressed-fill-alpha   = 0.24\n"
        "selection-fill-alpha = 0.35\n"
        "\n"
        "[popups]\n"
        f'background       = "{bg}"\n'
        "background-alpha = 0.96\n"
        f'text             = "{fg}"\n'
        'border           = "hyprland.active-border"\n'
        "border-alpha     = 1.0\n"
        f"border-width     = {border_w}\n"
        "\n"
        "[tooltip]\n"
        f'background       = "{bg}"\n'
        "background-alpha = 0.97\n"
        f'text             = "{fg}"\n'
        f'border           = "{accent2}"\n'
        "border-alpha     = 0.85\n"
        "\n"
        "[notifications]\n"
        f'background       = "{bg}"\n'
        "background-alpha = 0.97\n"
        f'text             = "{fg}"\n'
        'border           = "hyprland.active-border"\n'
        "border-alpha     = 1.0\n"
        f"border-width     = {border_w}\n"
        f'countdown        = "{accent2}"\n'
        "\n"
        "[launcher]\n"
        f'background                = "{bg}"\n'
        "background-alpha          = 0.95\n"
        f'text                      = "{fg}"\n'
        'border                    = "hyprland.active-border"\n'
        "border-alpha              = 1.0\n"
        f'scrim                     = "{darker_bg}"\n'
        f"scrim-alpha               = {scrim_alpha}\n"
        f'selected-background       = "{accent}"\n'
        f"selected-background-alpha = {sel_fill_alpha}\n"
        f'selected-text             = "{accent}"\n'
        'selected-border           = "hyprland.active-border"\n'
        "selected-border-alpha     = 0.60\n"
        "\n"
        "[menu]\n"
        f'background                = "{bg}"\n'
        "background-alpha          = 0.98\n"
        f'text                      = "{fg}"\n'
        'border                    = "hyprland.active-border"\n'
        "border-alpha              = 1.0\n"
        f'scrim                     = "{darker_bg}"\n'
        f"scrim-alpha               = {scrim_alpha}\n"
        f'selected-background       = "{accent}"\n'
        f"selected-background-alpha = {sel_fill_alpha}\n"
        f'selected-text             = "{accent}"\n'
        'selected-border           = "hyprland.active-border"\n'
        "selected-border-alpha     = 0.60\n"
        "\n"
        "[polkit]\n"
        f'background   = "{bg}"\n'
        "background-alpha = 0.98\n"
        f'text         = "{fg}"\n'
        f'text-error   = "{err}"\n'
        'border       = "hyprland.active-border"\n'
        f'border-error = "{err}"\n'
        "border-alpha = 1.0\n"
        f'scrim        = "{darker_bg}"\n'
        f"scrim-alpha  = {scrim_alpha}\n"
        f'accent       = "{accent}"\n'
        "\n"
        "[lock]\n"
        f'background       = "{bg}"\n'
        "background-alpha = 0.85\n"
        f'text             = "{fg}"\n'
        f'placeholder      = "{placeholder}"\n'
        f'text-error       = "{err}"\n'
        'border           = "hyprland.active-border"\n'
        f'border-active    = "{accent2}"\n'
        f'border-error     = "{err}"\n'
        "border-alpha     = 1.0\n"
        f'selection        = "{accent}"\n'
        "selection-alpha  = 0.40\n"
        "\n"
        "[image-picker]\n"
        f'text                    = "{fg}"\n'
        f'selected-border         = "{accent}"\n'
        "selected-border-alpha   = 1.0\n"
        f'unselected-border       = "{muted}"\n'
        "unselected-border-alpha = 0.35\n",
        encoding="utf-8",
    )
    return dst


def boot_logo(agent: dict, pal: dict[str, str]) -> Path:
    """800x188 transparent wordmark for the Plymouth boot splash."""
    theme = THEMES / agent["theme"]
    dst = theme / "unlock.png"
    accent = pal["accent"]
    accent2 = pal.get("icon_mark", agent["accent2"])
    # Plymouth splash is dark, so keep the boot wordmark bright even for light themes.
    fg = "#F2F6F8" if pal.get("mode") == "light" else pal.get("foreground", "#E8ECF2")

    name = fit_label(agent["name"].upper(), BEBAS, 96, fg, f"{agent['slug']}-logo", 680)
    _, nh = size(name)
    caption = label("V A L O R A N T", RAJ_SB, 17, accent, f"{agent['slug']}-cap")

    rule_w = 260
    left = (800 - rule_w) // 2
    split = left + int(rule_w * 0.68)
    block = nh + 10 + 6 + 12 + 17
    top = (188 - block) // 2
    cmd = ["magick", "-size", "800x188", "xc:none",
           "-gravity", "northwest", "-compose", "over",
           str(name), "-geometry", f"+{(800 - size(name)[0]) // 2}+{top}",
           "-composite",
           "-fill", accent, "-draw",
           f"rectangle {left},{top + nh + 10} {split},{top + nh + 16}",
           "-fill", accent2, "-draw",
           f"rectangle {split + 6},{top + nh + 10} {left + rule_w},{top + nh + 16}",
           str(caption),
           "-geometry", f"+{(800 - size(caption)[0]) // 2}+{top + nh + 28}",
           "-composite", str(dst)]
    run(cmd)
    return dst


def boot_preview(agent: dict, pal: dict[str, str], logo: Path) -> Path:
    """1920x1080 mock of the boot/lock screen, used by the plymouth picker."""
    theme = THEMES / agent["theme"]
    dst = theme / "preview-unlock.png"
    accent = pal["accent"]
    accent2 = pal.get("icon_mark", agent["accent2"])
    # Plymouth mock uses a dark canvas so unlock.png stays bright and readable.
    bg = "#0A0E14" if pal.get("mode") == "light" else pal["background"]
    muted = "#7F8C96" if pal.get("mode") == "light" else pal.get("dark_foreground", "#7F8C96")

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

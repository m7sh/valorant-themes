#!/usr/bin/env python3
"""
Build the VALORANT agent theme bundle.

Each agent gets an independent Omarchy theme whose palette comes from that
agent's signature ability and ultimate VFX colours. Wallpapers are re-encoded
to 4K WebP, and a branded signature wallpaper is composited from the agent's
official render.

Usage:
    python3 tools/build.py                # colours + all wallpapers
    python3 tools/build.py --no-walls     # colours only
    python3 tools/build.py --only jett    # one agent
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
ASSETS = ROOT / "assets"
PORTRAITS = ASSETS / "portraits"
FONTS = ASSETS / "fonts"
SOURCE_WALLS = Path("/home/mush/Downloads/valorant theme bundle wallpapers")

FONT_BEBAS = FONTS / "BebasNeue-Regular.ttf"
FONT_RAJ_B = FONTS / "Rajdhani-Bold.ttf"
FONT_RAJ_SB = FONTS / "Rajdhani-SemiBold.ttf"
FONT_RAJ_M = FONTS / "Rajdhani-Medium.ttf"

# slug, name, role, origin, protocol number, signature, ultimate,
# accent, accent2, base background, icon theme, source wallpaper filenames
AGENTS = [
    ("astra", "Astra", "Controller", "GHANA", "16", "Astral Form", "Cosmic Divide",
     "#A97BFF", "#FFD37A", "#0D0A1A", "Yaru-purple",
     ["astra1.png", "astra2.png", "astra3.png"]),
    ("breach", "Breach", "Initiator", "SWEDEN", "13", "Fault Line", "Rolling Thunder",
     "#F59E0B", "#FDE047", "#140F08", "Yaru-yellow",
     ["breach1.jpg"]),
    ("brimstone", "Brimstone", "Controller", "UNITED STATES", "01", "Sky Smoke", "Orbital Strike",
     "#FF6B2C", "#FFC15E", "#130C09", "Yaru-red",
     ["brimstone1.jpg"]),
    ("chamber", "Chamber", "Sentinel", "FRANCE", "18", "Rendezvous", "Tour De Force",
     "#E8C46A", "#4FD1C5", "#0A1014", "Yaru-yellow",
     ["chamber1.png", "chamber2.png"]),
    ("clove", "Clove", "Controller", "SCOTLAND", "25", "Ruse", "Not Dead Yet",
     "#FF7AC6", "#8BE8C4", "#150E15", "Yaru-magenta",
     ["clove1.jpeg"]),
    ("cypher", "Cypher", "Sentinel", "MOROCCO", "05", "Trapwire", "Neural Theft",
     "#2DD4E8", "#8AA4B8", "#081116", "Yaru-blue",
     ["cypher1.jpeg", "cypher2.png"]),
    ("deadlock", "Deadlock", "Sentinel", "NORWAY", "23", "GravNet", "Annihilation",
     "#8FD8E8", "#DCE8F0", "#0A1014", "Yaru-blue",
     []),
    ("fade", "Fade", "Initiator", "TURKIYE", "20", "Prowler", "Nightfall",
     "#E2453F", "#FF8A5C", "#120A0C", "Yaru-red",
     ["fade1.jpg"]),
    ("gekko", "Gekko", "Initiator", "UNITED STATES", "22", "Dizzy", "Thrash",
     "#B8F26B", "#2FD8C5", "#0A130B", "Yaru-olive",
     []),
    ("harbor", "Harbor", "Controller", "INDIA", "21", "Cove", "Reckoning",
     "#2FD0C8", "#4A9FE8", "#061318", "Yaru-prussiangreen",
     ["harbor1.jpg"]),
    ("hush", "Hush", "Duelist", "CHINA", "31", "Displacement", "Suspension",
     "#E85BB5", "#9D7BFF", "#160B16", "Yaru-magenta",
     []),
    ("iso", "Iso", "Duelist", "CHINA", "24", "Double Tap", "Kill Contract",
     "#8C6BFF", "#2AE6E0", "#0A091A", "Yaru-purple",
     ["iso1.jpeg"]),
    ("jett", "Jett", "Duelist", "SOUTH KOREA", "10", "Tailwind", "Blade Storm",
     "#B8F5E8", "#7FB8FF", "#0A1216", "Yaru-blue",
     ["jett1.jpg", "jett2.jpeg", "jett2.jpg", "jett2.png"]),
    ("kayo", "KAY/O", "Initiator", "ALTERNATE EARTH", "17", "ZERO/point", "NULL/cmd",
     "#3FA9FF", "#FF7A3D", "#080F1A", "Yaru-blue",
     ["kayo1.jpg"]),
    ("killjoy", "Killjoy", "Sentinel", "GERMANY", "04", "ALARMBOT", "Lockdown",
     "#FFD23F", "#9BE564", "#10110A", "Yaru-yellow",
     ["kj1.jpg", "kj2\\.jpg"]),
    ("miks", "Miks", "Controller", "CROATIA", "30", "M-pulse", "Bassquake",
     "#6FD8CE", "#A78BFA", "#0A1016", "Yaru-blue",
     []),
    ("neon", "Neon", "Duelist", "PHILIPPINES", "19", "High Gear", "Overdrive",
     "#22E0FF", "#FF2E97", "#08111C", "Yaru-blue",
     ["neon2.jpg", "neon3.jpg"]),
    ("omen", "Omen", "Controller", "UNKNOWN", "03", "Dark Cover", "From the Shadows",
     "#9270E8", "#5E94B1", "#0A0912", "Yaru-purple",
     ["omen1.jpg", "omen2.jpg"]),
    ("phoenix", "Phoenix", "Duelist", "ENGLAND", "09", "Curveball", "Run it Back",
     "#FF7A2F", "#FFD166", "#140B06", "Yaru-red",
     ["phoenix1.jpg", "phoenix2.jpg"]),
    ("raze", "Raze", "Duelist", "BRAZIL", "12", "Boom Bot", "Showstopper",
     "#FF8A1F", "#2BB3B8", "#12100A", "Yaru-red",
     ["raze1.jpg", "raze2.jpg"]),
    ("reyna", "Reyna", "Duelist", "MEXICO", "11", "Devour", "Empress",
     "#C44BE0", "#8B3FD6", "#140A18", "Yaru-magenta",
     ["reyna1.jpg"]),
    ("sage", "Sage", "Sentinel", "CHINA", "07", "Healing Orb", "Resurrection",
     "#45D6A5", "#BFEFE6", "#071311", "Yaru-sage",
     ["sage.jpg", "sage2.jpg", "sage3.jpg"]),
    ("skye", "Skye", "Initiator", "AUSTRALIA", "14", "Guiding Light", "Seekers",
     "#6FD88F", "#F2C14E", "#0B120C", "Yaru-sage",
     ["sky1.jpg", "sky2.png", "sky3.png"]),
    ("sova", "Sova", "Initiator", "RUSSIA", "06", "Recon Bolt", "Hunter's Fury",
     "#5AA9E6", "#9FB8D0", "#08101A", "Yaru-blue",
     ["sova1.jpeg"]),
    ("tejo", "Tejo", "Initiator", "COLOMBIA", "27", "Guided Salvo", "Armageddon",
     "#E0A84E", "#3FBFC0", "#12100A", "Yaru-yellow",
     []),
    ("veto", "Veto", "Sentinel", "SENEGAL", "29", "Interceptor", "Evolution",
     "#C2453F", "#4FA4B2", "#120B0C", "Yaru-red",
     []),
    ("viper", "Viper", "Controller", "UNITED STATES", "02", "Toxic Screen", "Viper's Pit",
     "#3FE05F", "#C8F542", "#07120A", "Yaru-sage",
     ["viper1.jpg", "viper2.jpg", "viper3.jpg", "viper.png"]),
    ("vyse", "Vyse", "Sentinel", "UNKNOWN", "26", "Arc Rose", "Steel Garden",
     "#7A3FF2", "#C24B5A", "#0C0A1A", "Yaru-purple",
     ["vyse1.jpg", "vyse2.jpg", "vyse3.jpg"]),
    ("waylay", "Waylay", "Duelist", "THAILAND", "28", "Refract", "Convergent Paths",
     "#A78BFA", "#67E8F9", "#0B0C1A", "Yaru-purple",
     []),
    ("yoru", "Yoru", "Duelist", "JAPAN", "15", "Gatecrash", "Dimensional Drift",
     "#3B5BFF", "#D94A3D", "#080C1A", "Yaru-blue",
     ["yoru1.jpg", "yoru.png"]),
]


# ----------------------------- colour helpers -----------------------------

def hx(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb(value: tuple[float, float, float]) -> str:
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c))) for c in value)


def mix(a: str, b: str, t: float) -> str:
    ca, cb = hx(a), hx(b)
    return rgb(tuple(ca[i] * (1 - t) + cb[i] * t for i in range(3)))


def blend(a: str, b: str) -> str:
    """Simple screen blend, good for glowing accents on dark backgrounds."""
    ca, cb = hx(a), hx(b)
    return rgb(tuple(255 - (255 - ca[i]) * (255 - cb[i]) / 255 for i in range(3)))


def make_palette(accent: str, accent2: str, background: str) -> dict[str, str]:
    base = {
        "red": "#F06A6A", "yellow": "#E8C55C", "orange": "#E8944A",
        "green": "#6FCF97", "cyan": "#56C8D8", "blue": "#6A9BFF",
        "magenta": "#C77DFF", "brown": "#9C6B4A",
    }
    bright = {
        "bright_red": "#FF8A8A", "bright_yellow": "#FFE08A",
        "bright_green": "#9BEFB8", "bright_cyan": "#8AE8F2",
        "bright_blue": "#9CC0FF", "bright_magenta": "#E3A6FF",
        "bright_orange": "#FFB37A", "bright_brown": "#C99772",
    }
    foreground = mix("#E9ECF2", accent, 0.10)
    bright_foreground = mix("#FFFFFF", accent, 0.07)

    p: dict[str, str] = {
        "mode": "dark",
        "accent": accent,
        "selection": mix(background, accent, 0.30),
        "muted": mix(background, foreground, 0.38),
        "background": background,
        "dark_background": mix(background, "#000000", 0.34),
        "darker_background": mix(background, "#000000", 0.55),
        "lighter_background": mix(background, accent, 0.10),
        "foreground": foreground,
        "dark_foreground": mix(foreground, background, 0.58),
        "light_foreground": mix(foreground, "#FFFFFF", 0.22),
        "bright_foreground": bright_foreground,
    }
    for name, value in base.items():
        tinted = mix(value, accent, 0.22)
        p[name] = tinted
        p["bright_" + name] = mix(bright["bright_" + name], accent2, 0.18)
    # A little separation between normal and bright black-family slots.
    p["brown"] = mix(base["brown"], accent2, 0.10)
    return p


COLOR_ORDER = [
    "mode", "accent", "selection", "muted",
    "background", "dark_background", "darker_background", "lighter_background",
    "foreground", "dark_foreground", "light_foreground", "bright_foreground",
    "red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown",
    "bright_red", "bright_yellow", "bright_green", "bright_cyan", "bright_blue",
    "bright_magenta",
]


def write_colors(slug: str, accent: str, accent2: str, bg: str) -> None:
    theme = THEMES / f"valorant-{slug}"
    theme.mkdir(parents=True, exist_ok=True)
    palette = make_palette(accent, accent2, bg)
    lines = []
    for key in COLOR_ORDER:
        value = palette[key]
        lines.append(f'{key} = "{value}"' if key != "mode" else f'mode = "{value}"')
    (theme / "colors.toml").write_text("\n\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------ wallpapers ------------------------------

def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def export_wallpaper(src: Path, dst: Path) -> None:
    run([
        "magick", str(src), "-auto-orient", "-strip",
        "-resize", "5120x5120>", "-quality", "92",
        "-define", "webp:method=6", str(dst),
    ])


def signature_wallpaper(agent: dict, clean: bool, dst: Path) -> None:
    """Composite a 3840x2160 wallpaper from the official agent render."""
    slug = agent["slug"]
    portrait = PORTRAITS / f"{slug}.png"
    if not portrait.exists():
        raise SystemExit(f"missing portrait for {slug}: {portrait}")

    accent = agent["accent"]
    accent2 = agent["accent2"]
    bg = agent["background"]
    name = agent["name"].upper()
    role = agent["role"].upper()
    origin = agent["origin"]
    sig = agent["signature"].upper()
    ult = agent["ultimate"].upper()
    num = agent["number"]

    base = Path(f"/tmp/opencode/vt-{slug}-base.png")
    beams = Path(f"/tmp/opencode/vt-{slug}-beams.png")
    halo = Path(f"/tmp/opencode/vt-{slug}-halo.png")

    # Base: accent bloom on the right, darkened left column for type.
    run([
        "magick", "-size", "960x540", f"xc:{bg}",
        "(", "-size", "960x540", f"radial-gradient:{accent}55-{accent}00", ")",
        "-compose", "over", "-composite",
        "(", "-size", "960x540", "xc:none", "-fill", bg,
        "-draw", "rectangle 0,0 430,540", "-blur", "0x45", ")",
        "-compose", "over", "-composite",
        "-resize", "3840x2160!", str(base),
    ])

    if not clean:
        # Accent speed lines.
        run([
            "magick", "-size", "1920x1080", "xc:none", "-fill", accent, "-stroke", "none",
            "-draw", "polygon 0,720 520,620 660,645 60,775",
            "-draw", "polygon 0,810 390,725 500,744 30,850",
            "-blur", "0x4", "-channel", "A", "-evaluate", "multiply", "0.18", "+channel",
            "-resize", "3840x2160!", str(beams),
        ])
        wallpaper = [str(base), str(beams)]
        compose = ["-compose", "over", "-composite"]
    else:
        wallpaper = [str(base)]
        compose = []

    # Halo behind the portrait.
    run([
        "magick", "-size", "1100x1100", "xc:none", "-fill", accent,
        "-draw", "circle 550,550 550,120", "-blur", "0x100",
        "-channel", "A", "-evaluate", "multiply", "0.32", "+channel",
        "-resize", "1900x1900", str(halo),
    ])

    cmd = ["magick", *wallpaper, *compose]
    cmd += [str(halo), "-geometry", "+2380+430", "-compose", "over", "-composite"]
    # Trim the transparent padding so every render is framed consistently:
    # bottom-anchored, full height, and pinned to a fixed right margin.
    cmd += ["(", str(portrait), "-filter", "Lanczos", "-trim", "+repage",
            "-resize", "x2040", ")"]
    cmd += ["-gravity", "northeast", "-geometry", "+60+120",
            "-compose", "over", "-composite"]

    if not clean:
        # Left scrim keeps type legible when a wide render reaches into the
        # text column.
        scrim = Path(f"/tmp/opencode/vt-{slug}-scrim.png")
        run([
            "magick", "-size", "1920x1080", "xc:none", "-fill", bg,
            "-draw", "rectangle 0,0 610,1080", "-blur", "0x70",
            "-channel", "A", "-evaluate", "multiply", "0.94", "+channel",
            "-resize", "3840x2160!", str(scrim),
        ])
        cmd += [str(scrim), "-gravity", "northwest",
                "-compose", "over", "-composite"]

    if not clean:
        def label(text: str, font: Path, pointsize: int, fill: str, tag: str) -> Path:
            p = Path(f"/tmp/opencode/vt-{slug}-{tag}.png")
            run([
                "magick", "-background", "none", "-fill", fill,
                "-font", str(font), "-pointsize", str(pointsize),
                f"label:{text}", "-trim", "+repage", str(p),
            ])
            return p

        def size(p: Path) -> tuple[int, int]:
            out = subprocess.run(
                ["magick", "identify", "-format", "%w %h", str(p)],
                check=True, capture_output=True, text=True,
            ).stdout.split()
            return int(out[0]), int(out[1])

        eyebrow = label(f"// VALORANT PROTOCOL   ·   AGENT {num}",
                        FONT_RAJ_SB, 34, accent, "eyebrow")
        name_img = label(name, FONT_BEBAS, 370, "#FFFFFF", "name")
        nw, nh = size(name_img)
        if nw > 1180:
            scale = 1180 / nw
            run(["magick", str(name_img), "-resize", f"{1180}x",
                 "-filter", "Lanczos", "+repage", str(name_img)])
            nw, nh = size(name_img)
        role_img = label(f"{role}   //   {origin}", FONT_RAJ_B, 58, accent, "role")
        _, rh = size(role_img)
        sig_label = label("SIGNATURE", FONT_RAJ_SB, 31, "#7F8C96", "sig-label")
        sig_img = label(sig, FONT_BEBAS, 130, "#F2F6F8", "sig")
        ult_label = label("ULTIMATE", FONT_RAJ_SB, 31, "#7F8C96", "ult-label")
        ult_img = label(ult, FONT_BEBAS, 96, accent2, "ult")
        footer = label("VALORANT  //  AGENT THEMES", FONT_RAJ_M, 26, accent, "footer")

        role_y = 330 + nh + 34
        rule_y = role_y + rh + 44

        cmd += ["-gravity", "northwest", "-compose", "over"]
        for img, x, y in (
            (eyebrow, 220, 186),
            (name_img, 206, 330),
            (role_img, 222, role_y),
            (sig_label, 220, 1000),
            (sig_img, 212, 1075),
            (ult_label, 220, 1310),
            (ult_img, 212, 1370),
            (footer, 220, 1990),
        ):
            cmd += [str(img), "-geometry", f"+{x}+{y}", "-composite"]
        cmd += ["-fill", accent, "-draw", f"rectangle 222,{rule_y} 640,{rule_y + 8}"]

    cmd += ["-quality", "92", "-define", "webp:method=6", str(dst)]
    run(cmd)


def build_walls(agent: dict, only_generated: bool = False) -> None:
    theme = THEMES / f"valorant-{agent['slug']}"
    bgdir = theme / "backgrounds"
    if bgdir.exists():
        shutil.rmtree(bgdir)
    bgdir.mkdir(parents=True, exist_ok=True)

    # Branded 4K signature wallpaper first, so it is the default background.
    signature_wallpaper(agent, clean=False, dst=bgdir / f"0-{agent['slug']}-signature.webp")

    if only_generated:
        return

    index = 1
    if not agent["sources"]:
        # No collected art: add a clean companion piece.
        signature_wallpaper(agent, clean=True, dst=bgdir / f"1-{agent['slug']}-clean.webp")
        return

    for original in agent["sources"]:
        src = SOURCE_WALLS / original
        if not src.exists():
            print(f"  ! missing wallpaper {src}", file=sys.stderr)
            continue
        stem = original.rsplit(".", 1)[0].replace("\\", "").replace(" ", "-")
        dst = bgdir / f"{index}-{stem}.webp"
        export_wallpaper(src, dst)
        index += 1


# -------------------------------- build --------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="build one agent slug")
    parser.add_argument("--no-walls", action="store_true")
    parser.add_argument("--generated-walls-only", action="store_true")
    args = parser.parse_args()

    THEMES.mkdir(exist_ok=True)
    manifest = []
    agents = [a for a in AGENTS if not args.only or a[0] == args.only]
    if not agents:
        raise SystemExit(f"unknown agent: {args.only}")

    for (slug, name, role, origin, number, sig, ult, accent, accent2, bg, icon, sources) in agents:
        print(f"== {name}")
        write_colors(slug, accent, accent2, bg)
        theme = THEMES / f"valorant-{slug}"
        (theme / "icons.theme").write_text(icon + "\n", encoding="utf-8")
        if not args.no_walls:
            build_walls(
                {
                    "slug": slug, "name": name, "role": role, "origin": origin,
                    "number": number, "signature": sig, "ultimate": ult,
                    "accent": accent, "accent2": accent2, "background": bg,
                    "sources": sources,
                },
                only_generated=args.generated_walls_only,
            )
        manifest.append({
            "slug": slug,
            "theme": f"valorant-{slug}",
            "name": name,
            "role": role,
            "origin": origin,
            "number": number,
            "signature": sig,
            "ultimate": ult,
            "accent": accent,
            "accent2": accent2,
            "background": bg,
        })

    if not args.only:
        (ROOT / "agents.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    print(f"built {len(manifest)} theme(s)")


if __name__ == "__main__":
    main()

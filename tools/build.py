#!/usr/bin/env python3
"""
Build the VALORANT agent theme bundle.

Each agent gets an independent Omarchy theme with a distinct color personality
derived from its abilities, aesthetic, and role (including select light-mode
variants), plus a role-themed 4K signature wallpaper.

Usage:
    python3 tools/build.py                # colours + signature wallpapers
    python3 tools/build.py --no-walls     # colours only
    python3 tools/build.py --only jett    # one agent
"""
from __future__ import annotations

import argparse
import colorsys
import json
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
     "#B48CFF", "#FFD470", "#0A0818", "Yaru-purple",
     ["astra1.png", "astra2.png", "astra3.png"]),
    ("breach", "Breach", "Initiator", "SWEDEN", "13", "Fault Line", "Rolling Thunder",
     "#F59E0B", "#FFE066", "#16110C", "Yaru-yellow",
     ["breach1.jpg"]),
    ("brimstone", "Brimstone", "Controller", "UNITED STATES", "01", "Sky Smoke", "Orbital Strike",
     "#FF6B2C", "#F4C462", "#11130E", "Yaru-red",
     ["brimstone1.jpg"]),
    ("chamber", "Chamber", "Sentinel", "FRANCE", "18", "Rendezvous", "Tour De Force",
     "#ECC86E", "#38D9C0", "#0C1018", "Yaru-yellow",
     ["chamber1.png", "chamber2.png"]),
    ("clove", "Clove", "Controller", "SCOTLAND", "25", "Ruse", "Not Dead Yet",
     "#FF6EC7", "#6DF0C2", "#170E18", "Yaru-magenta",
     ["clove1.jpeg"]),
    ("cypher", "Cypher", "Sentinel", "MOROCCO", "05", "Trapwire", "Neural Theft",
     "#2CE2F2", "#D8A85A", "#11110E", "Yaru-blue",
     ["cypher1.jpeg", "cypher2.png"]),
    ("deadlock", "Deadlock", "Sentinel", "NORWAY", "23", "GravNet", "Annihilation",
     "#7EE2F8", "#E2F0F8", "#0D1318", "Yaru-blue",
     []),
    ("fade", "Fade", "Initiator", "TURKIYE", "20", "Prowler", "Nightfall",
     "#F03E4D", "#FF8A54", "#09070B", "Yaru-red",
     ["fade1.jpg"]),
    ("gekko", "Gekko", "Initiator", "UNITED STATES", "22", "Dizzy", "Thrash",
     "#B8FA4F", "#1CE5C8", "#0C140C", "Yaru-olive",
     []),
    ("harbor", "Harbor", "Controller", "INDIA", "21", "Cove", "Reckoning",
     "#28DFD5", "#F2C15A", "#061519", "Yaru-prussiangreen",
     ["harbor1.jpg"]),
    ("hush", "Hush", "Duelist", "CHINA", "31", "Displacement", "Suspension",
     "#F25CC4", "#A77BFF", "#150B16", "Yaru-magenta",
     []),
    ("iso", "Iso", "Duelist", "CHINA", "24", "Double Tap", "Kill Contract",
     "#8E6BFF", "#22F0E8", "#09091A", "Yaru-purple",
     ["iso1.jpeg"]),
    ("jett", "Jett", "Duelist", "SOUTH KOREA", "10", "Tailwind", "Blade Storm",
     "#0984E3", "#0D9F93", "#EFF5F9", "Yaru-blue",
     ["jett1.jpg", "jett2.jpeg", "jett2.jpg", "jett2.png"]),
    ("kayo", "KAY/O", "Initiator", "ALTERNATE EARTH", "17", "ZERO/point", "NULL/cmd",
     "#33A8FF", "#FF6A2B", "#0A1018", "Yaru-blue",
     ["kayo1.jpg"]),
    ("killjoy", "Killjoy", "Sentinel", "GERMANY", "04", "ALARMBOT", "Lockdown",
     "#FFD633", "#FF4F8B", "#0F121D", "Yaru-yellow",
     ["kj1.jpg", "kj2\\.jpg"]),
    ("miks", "Miks", "Controller", "CROATIA", "30", "M-pulse", "Bassquake",
     "#4AE8D0", "#B07AFF", "#0B0F1A", "Yaru-blue",
     []),
    ("neon", "Neon", "Duelist", "PHILIPPINES", "19", "High Gear", "Overdrive",
     "#00E5FF", "#FF2A9D", "#070F1C", "Yaru-blue",
     ["neon2.jpg", "neon3.jpg"]),
    ("omen", "Omen", "Controller", "UNKNOWN", "03", "Dark Cover", "From the Shadows",
     "#708CFF", "#4CC3D9", "#080A0F", "Yaru-purple",
     ["omen1.jpg", "omen2.jpg"]),
    ("phoenix", "Phoenix", "Duelist", "ENGLAND", "09", "Curveball", "Run it Back",
     "#FF6A1A", "#FFD447", "#120A07", "Yaru-red",
     ["phoenix1.jpg", "phoenix2.jpg"]),
    ("raze", "Raze", "Duelist", "BRAZIL", "12", "Boom Bot", "Showstopper",
     "#FF841F", "#20D6C7", "#14100D", "Yaru-red",
     ["raze1.jpg", "raze2.jpg"]),
    ("reyna", "Reyna", "Duelist", "MEXICO", "11", "Devour", "Empress",
     "#DF42F5", "#FF7AD4", "#120816", "Yaru-magenta",
     ["reyna1.jpg"]),
    ("sage", "Sage", "Sentinel", "CHINA", "07", "Healing Orb", "Resurrection",
     "#0B8F63", "#187FA1", "#EEF5F1", "Yaru-sage",
     ["sage.jpg", "sage2.jpg", "sage3.jpg"]),
    ("skye", "Skye", "Initiator", "AUSTRALIA", "14", "Guiding Light", "Seekers",
     "#5CE084", "#F5C443", "#0A140D", "Yaru-sage",
     ["sky1.jpg", "sky2.png", "sky3.png"]),
    ("sova", "Sova", "Initiator", "RUSSIA", "06", "Recon Bolt", "Hunter's Fury",
     "#4BB2FF", "#E5B85C", "#09111B", "Yaru-blue",
     ["sova1.jpeg"]),
    ("tejo", "Tejo", "Initiator", "COLOMBIA", "27", "Guided Salvo", "Armageddon",
     "#E8A838", "#2EC4B6", "#14100C", "Yaru-yellow",
     []),
    ("veto", "Veto", "Sentinel", "SENEGAL", "29", "Interceptor", "Evolution",
     "#E04842", "#48B8C4", "#140B0D", "Yaru-red",
     []),
    ("viper", "Viper", "Controller", "UNITED STATES", "02", "Toxic Screen", "Viper's Pit",
     "#2EE858", "#C8FF2E", "#060E08", "Yaru-sage",
     ["viper1.jpg", "viper2.jpg", "viper3.jpg", "viper.png"]),
    ("vyse", "Vyse", "Sentinel", "UNKNOWN", "26", "Arc Rose", "Steel Garden",
     "#E24A7A", "#8E52FF", "#0D0C14", "Yaru-purple",
     ["vyse1.jpg", "vyse2.jpg", "vyse3.jpg"]),
    ("waylay", "Waylay", "Duelist", "THAILAND", "28", "Refract", "Convergent Paths",
     "#6A3DF5", "#068FA8", "#F4F1FA", "Yaru-purple",
     []),
    ("yoru", "Yoru", "Duelist", "JAPAN", "15", "Gatecrash", "Dimensional Drift",
     "#3B6BFF", "#FF3B5C", "#070B19", "Yaru-blue",
     ["yoru1.jpg", "yoru.png"]),
]

# Per-agent bespoke syntax & surface personalities so each agent's editor,
# terminal, and btop colors carry a distinct character instead of sharing one
# 22%-blended base palette.
# Keys: mode, fg_base, bright_boost, syntax=(red, yellow, orange, green, cyan, blue, magenta, brown)
PALETTE_PROFILES: dict[str, dict] = {
    # Cosmic indigo + starlight gold
    "astra": {
        "mode": "dark", "fg_base": "#EBE7FA", "bright_boost": 0.16,
        "syntax": ("#F06490", "#FFD470", "#FF9955", "#4CE0B8", "#5CD2F5", "#7E8CFF", "#C878FF", "#9E765E"),
    },
    # Industrial tungsten + magma amber
    "breach": {
        "mode": "dark", "fg_base": "#F3ECE2", "bright_boost": 0.14,
        "syntax": ("#F25E4B", "#F5B82E", "#FF8B3D", "#8CCF6B", "#5AC4B8", "#6C9BD2", "#CC7BA8", "#A87449"),
    },
    # Tactical olive-charcoal + orbital ember
    "brimstone": {
        "mode": "dark", "fg_base": "#ECEBE2", "bright_boost": 0.14,
        "syntax": ("#EB5E47", "#E6B84C", "#FF6B2C", "#7AC26B", "#52B8B0", "#6899C8", "#C47CA6", "#9E734E"),
    },
    # Tailored Parisian navy + champagne gold + arc teal
    "chamber": {
        "mode": "dark", "fg_base": "#EDF0F7", "bright_boost": 0.15,
        "syntax": ("#E65C6E", "#ECC86E", "#E08B4F", "#4EC996", "#38D9C0", "#6B9BF2", "#C484E8", "#A17958"),
    },
    # Dusk plum + immortal rose + spectral mint
    "clove": {
        "mode": "dark", "fg_base": "#F6EAF3", "bright_boost": 0.17,
        "syntax": ("#FF5D8F", "#FAD06B", "#FF9466", "#6DF0C2", "#6AE0F0", "#8CA6FF", "#FF6EC7", "#A37268"),
    },
    # Moroccan slate-sand + trapwire cyan + brass
    "cypher": {
        "mode": "dark", "fg_base": "#EAECE6", "bright_boost": 0.14,
        "syntax": ("#E86862", "#D8A85A", "#E38B4D", "#54C99A", "#2CE2F2", "#5DA3E8", "#B582DF", "#9C7551"),
    },
    # Arctic gunmetal + glacier ice (cool steel monochrome-adjacent)
    "deadlock": {
        "mode": "dark", "fg_base": "#E4EEF4", "bright_boost": 0.15,
        "syntax": ("#E06C82", "#D8C984", "#DF9668", "#6AC9AA", "#7EE2F8", "#6FA9EC", "#AE8FE8", "#8B7468"),
    },
    # Nightmare obsidian + crimson terror + ember
    "fade": {
        "mode": "dark", "fg_base": "#EFE8EC", "bright_boost": 0.16,
        "syntax": ("#F03E4D", "#DFB256", "#FF7E47", "#55BA8E", "#59B6C9", "#6B87DB", "#C266D6", "#946458"),
    },
    # Street-art olive + dizzy acid lime + thrash teal
    "gekko": {
        "mode": "dark", "fg_base": "#EAF5E6", "bright_boost": 0.18,
        "syntax": ("#FF5C6C", "#E2F24B", "#FF9C3B", "#B8FA4F", "#1CE5C8", "#57A6FF", "#D670FF", "#9A7A50"),
    },
    # Deep monsoon teal + lotus gold
    "harbor": {
        "mode": "dark", "fg_base": "#E3F2F2", "bright_boost": 0.15,
        "syntax": ("#EA6B6B", "#F2C15A", "#EB8E52", "#3CD9A0", "#28DFD5", "#4D9FE8", "#B884EB", "#9A7254"),
    },
    # Velvet twilight + neon orchid
    "hush": {
        "mode": "dark", "fg_base": "#F3E8F4", "bright_boost": 0.16,
        "syntax": ("#F25484", "#EDC46B", "#F08B5D", "#5CD6A8", "#59D1EB", "#8194FF", "#F25CC4", "#9E6D6B"),
    },
    # Cyber arena void + ultraviolet + shield cyan
    "iso": {
        "mode": "dark", "fg_base": "#EAE9FA", "bright_boost": 0.17,
        "syntax": ("#FF5484", "#F2CF5E", "#FF8F4D", "#42E3A4", "#22F0E8", "#668AFF", "#8E6BFF", "#966E68"),
    },
    # LIGHT MODE — Cloud mist + tailwind sky + blade teal
    "jett": {
        "mode": "light", "fg_base": "#15222E", "bright_boost": -0.08,
        "syntax": ("#C92A42", "#9C6500", "#C44D0E", "#0E7A4D", "#0A7385", "#0984E3", "#8C2EA8", "#6E4726"),
    },
    # Titanium chassis + suppress blue + overload orange
    "kayo": {
        "mode": "dark", "fg_base": "#E6EEF7", "bright_boost": 0.15,
        "syntax": ("#F05959", "#EBC14D", "#FF6A2B", "#4DD498", "#3DC7EB", "#33A8FF", "#AC7EFF", "#947056"),
    },
    # Blueprint navy + hazard yellow + turret raspberry
    "killjoy": {
        "mode": "dark", "fg_base": "#EEF0FA", "bright_boost": 0.17,
        "syntax": ("#FF4F8B", "#FFD633", "#FF9138", "#5CE07E", "#38D4EE", "#4D94FF", "#B870FF", "#A17654"),
    },
    # Deep bass navy + synth mint + violet pulse
    "miks": {
        "mode": "dark", "fg_base": "#E7F2F5", "bright_boost": 0.16,
        "syntax": ("#F25C7A", "#EBD063", "#F28F52", "#4AE8B0", "#4AE8D0", "#5E9CFF", "#B07AFF", "#96735D"),
    },
    # High-voltage deep blue + overdrive cyan + hot magenta
    "neon": {
        "mode": "dark", "fg_base": "#E6F4FA", "bright_boost": 0.18,
        "syntax": ("#FF3B6B", "#FFE838", "#FF8826", "#2EF29B", "#00E5FF", "#3D8BFF", "#FF2A9D", "#A1715A"),
    },
    # Abyssal smoke — moody cool indigo/slate monochrome-adjacent
    "omen": {
        "mode": "dark", "fg_base": "#E2E8F2", "bright_boost": 0.13,
        "syntax": ("#D46B84", "#C9B57A", "#C98C66", "#6EB8A0", "#4CC3D9", "#708CFF", "#9B84E8", "#886D5B"),
    },
    # Charred obsidian + blaze orange + solar gold
    "phoenix": {
        "mode": "dark", "fg_base": "#F5ECE6", "bright_boost": 0.17,
        "syntax": ("#FF4D4D", "#FFD447", "#FF6A1A", "#78D66E", "#4BC7C4", "#6699F2", "#D670C8", "#AD7449"),
    },
    # Scrapyard warm dark + street-graffiti pop
    "raze": {
        "mode": "dark", "fg_base": "#F5EFE8", "bright_boost": 0.18,
        "syntax": ("#FF5263", "#FFD93D", "#FF841F", "#5EE66D", "#20D6C7", "#4D9BFF", "#FF54B0", "#AD764D"),
    },
    # Soul obsidian + empress magenta + rose
    "reyna": {
        "mode": "dark", "fg_base": "#F4E8F6", "bright_boost": 0.16,
        "syntax": ("#F54E7B", "#ECC668", "#F08556", "#58D19F", "#52CAE0", "#7D8EFF", "#DF42F5", "#9B6B62"),
    },
    # LIGHT MODE — Jade alabaster + healing emerald + glacier teal
    "sage": {
        "mode": "light", "fg_base": "#14261F", "bright_boost": -0.08,
        "syntax": ("#C23646", "#9A690A", "#BA5114", "#0B8F63", "#107788", "#1F62A6", "#813FA6", "#664830"),
    },
    # Deep eucalyptus + verdant trail + sunlit ochre
    "skye": {
        "mode": "dark", "fg_base": "#E8F3EB", "bright_boost": 0.15,
        "syntax": ("#E86464", "#F5C443", "#E88C43", "#5CE084", "#40CCB8", "#5CA0E6", "#BA7EE0", "#9E764E"),
    },
    # Tundra night + recon azure + hunter gold
    "sova": {
        "mode": "dark", "fg_base": "#E5EEF7", "bright_boost": 0.15,
        "syntax": ("#EA636A", "#E5B85C", "#E88B4D", "#58CC9B", "#4EC6E8", "#4BB2FF", "#AE84EB", "#947256"),
    },
    # Volcanic basalt + salvo brass + tactical cyan
    "tejo": {
        "mode": "dark", "fg_base": "#F3EDE4", "bright_boost": 0.15,
        "syntax": ("#EC5B52", "#E8A838", "#F07E3D", "#60C98D", "#2EC4B6", "#5B9CE0", "#C47BD6", "#A37449"),
    },
    # Dark mahogany + interceptor crimson + steel teal
    "veto": {
        "mode": "dark", "fg_base": "#F2E9EA", "bright_boost": 0.15,
        "syntax": ("#E04842", "#E3BA59", "#EB7E4B", "#52C498", "#48B8C4", "#6694E3", "#C774C4", "#996B56"),
    },
    # Chem-lab black + toxic emerald + pit chartreuse
    "viper": {
        "mode": "dark", "fg_base": "#E3F2E7", "bright_boost": 0.17,
        "syntax": ("#E85D68", "#C8FF2E", "#E89B3C", "#2EE858", "#2CE0B8", "#4BA8D8", "#A87CE8", "#8C744A"),
    },
    # Liquid metal + arc rose + thorn violet
    "vyse": {
        "mode": "dark", "fg_base": "#EFEBF5", "bright_boost": 0.16,
        "syntax": ("#E24A7A", "#E3C16B", "#EB855B", "#52C99E", "#52C2DB", "#7392F2", "#8E52FF", "#966D62"),
    },
    # LIGHT MODE — Prismatic ivory + refract violet + prism cyan
    "waylay": {
        "mode": "light", "fg_base": "#1A152B", "bright_boost": -0.08,
        "syntax": ("#C92E63", "#9E6000", "#C74C12", "#0F7A54", "#067B91", "#334EC9", "#6A3DF5", "#6B452C"),
    },
    # Midnight Tokyo + rift cobalt + Oni crimson
    "yoru": {
        "mode": "dark", "fg_base": "#E7ECFA", "bright_boost": 0.17,
        "syntax": ("#FF3B5C", "#F0C456", "#FF7A45", "#45D4A0", "#38C8F0", "#3B6BFF", "#B866FF", "#946A5E"),
    },
}

COLOR_ORDER = [
    "mode", "accent", "selection", "muted",
    "background", "dark_background", "darker_background", "lighter_background",
    "foreground", "dark_foreground", "light_foreground", "bright_foreground",
    "selection_foreground", "selection_background",
    "hyprland_active_border", "hyprland_inactive_border", "icon_mark",
    "red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown",
    "bright_red", "bright_yellow", "bright_green", "bright_cyan", "bright_blue",
    "bright_magenta",
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


def rgba_hex(value: str, alpha_hex: str = "ee") -> str:
    return f"rgba({value.lstrip('#').lower()}{alpha_hex})"


def luminance(hex_color: str) -> float:
    def channel(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = hx(hex_color)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def shift_lightness(hex_color: str, delta: float) -> str:
    r, g, b = [c / 255.0 for c in hx(hex_color)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    nl = max(0.02, min(0.98, l + delta))
    nr, ng, nb = colorsys.hls_to_rgb(h, nl, s)
    return rgb((nr * 255, ng * 255, nb * 255))


def ensure_contrast(color: str, bg: str, min_ratio: float, light_mode: bool) -> str:
    if contrast_ratio(color, bg) >= min_ratio:
        return color
    r, g, b = [c / 255.0 for c in hx(color)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    step = -0.02 if light_mode else 0.02
    for _ in range(45):
        l = max(0.03, min(0.97, l + step))
        nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
        candidate = rgb((nr * 255, ng * 255, nb * 255))
        if contrast_ratio(candidate, bg) >= min_ratio:
            return candidate
    return candidate


def make_palette(slug: str, accent: str, accent2: str, background: str) -> dict[str, str]:
    prof = PALETTE_PROFILES[slug]
    mode = prof["mode"]
    light_mode = mode == "light"
    fg_base = prof["fg_base"]
    boost = prof["bright_boost"]
    syn = prof["syntax"]

    accent_c = ensure_contrast(accent, background, 4.5, light_mode)
    accent2_c = ensure_contrast(accent2, background, 3.8, light_mode)
    foreground = ensure_contrast(fg_base, background, 8.5, light_mode)

    if light_mode:
        dark_bg = mix(background, "#000000", 0.05)
        darker_bg = mix(background, "#000000", 0.11)
        lighter_bg = mix(background, "#FFFFFF", 0.58)
        selection = mix(background, accent_c, 0.18)
        muted = mix(background, foreground, 0.44)
        dark_fg = ensure_contrast(mix(foreground, background, 0.46), background, 3.6, True)
        light_fg = ensure_contrast(mix(foreground, background, 0.16), background, 6.5, True)
        bright_fg = ensure_contrast(mix(foreground, "#000000", 0.25), background, 11.0, True)
        sel_fg = foreground
        sel_bg = mix(background, accent_c, 0.24)
        inactive_border = rgba_hex(mix(background, foreground, 0.22), "aa")
    else:
        dark_bg = mix(background, "#000000", 0.34)
        darker_bg = mix(background, "#000000", 0.56)
        lighter_bg = mix(background, accent_c, 0.12)
        selection = mix(background, accent_c, 0.28)
        muted = mix(background, foreground, 0.42)
        dark_fg = ensure_contrast(mix(foreground, background, 0.46), background, 3.6, False)
        light_fg = ensure_contrast(mix(foreground, "#FFFFFF", 0.20), background, 10.5, False)
        bright_fg = ensure_contrast(mix(foreground, "#FFFFFF", 0.55), background, 12.5, False)
        sel_fg = bright_fg
        sel_bg = mix(background, accent_c, 0.32)
        inactive_border = rgba_hex(mix(background, foreground, 0.24), "aa")

    names = ("red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown")
    p: dict[str, str] = {
        "mode": mode,
        "accent": accent_c,
        "selection": selection,
        "muted": muted,
        "background": background,
        "dark_background": dark_bg,
        "darker_background": darker_bg,
        "lighter_background": lighter_bg,
        "foreground": foreground,
        "dark_foreground": dark_fg,
        "light_foreground": light_fg,
        "bright_foreground": bright_fg,
        "selection_foreground": sel_fg,
        "selection_background": sel_bg,
        "hyprland_active_border": f"{rgba_hex(accent_c, 'ee')} {rgba_hex(accent2_c, 'ee')} 45deg",
        "hyprland_inactive_border": inactive_border,
        "icon_mark": accent2_c,
    }
    for key, val in zip(names, syn):
        min_r = 3.4 if key == "brown" else 4.5
        base_col = ensure_contrast(val, background, min_r, light_mode)
        p[key] = base_col
        if key not in ("orange", "brown"):
            bright_col = shift_lightness(base_col, boost)
            # Subtle harmonic pull toward accent2 on bright slots without losing hue separation.
            bright_col = mix(bright_col, accent2_c, 0.10)
            p["bright_" + key] = ensure_contrast(bright_col, background, 4.8, light_mode)
    return p


def write_colors(slug: str, accent: str, accent2: str, bg: str) -> dict[str, str]:
    theme = THEMES / f"valorant-{slug}"
    theme.mkdir(parents=True, exist_ok=True)
    palette = make_palette(slug, accent, accent2, bg)
    lines = [f'{key} = "{palette[key]}"' for key in COLOR_ORDER]
    (theme / "colors.toml").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    return palette


# ------------------------------ wallpapers ------------------------------

def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def export_wallpaper(src: Path, dst: Path) -> None:
    run([
        "magick", str(src), "-auto-orient", "-strip",
        "-resize", "5120x5120>", "-quality", "92",
        "-define", "webp:method=6", str(dst),
    ])


def role_motif_commands(role: str, accent: str, accent2: str, light_mode: bool) -> list[str]:
    """Return ImageMagick 1920x1080 vector overlay args unique to each role."""
    a_alpha = "0.26" if not light_mode else "0.20"
    b_alpha = "0.18" if not light_mode else "0.14"
    # Render on 1920x1080 and scale up cleanly.
    if role == "DUELIST":
        return [
            "(", "-size", "1920x1080", "xc:none",
            "-fill", accent, "-stroke", "none",
            "-draw", "polygon 0,835 920,565 1045,585 0,900",
            "-draw", "polygon 180,960 1120,660 1185,672 220,995",
            "-fill", accent2,
            "-draw", "polygon 1360,0 1920,210 1920,248 1280,0",
            "-blur", "0x2", "-channel", "A", "-evaluate", "multiply", a_alpha, "+channel",
            "-resize", "3840x2160!", ")",
            "-compose", "over", "-composite",
        ]
    if role == "CONTROLLER":
        return [
            "(", "-size", "1920x1080", "xc:none",
            "-fill", "none", "-stroke", accent, "-strokewidth", "3",
            "-draw", "circle 1440,540 1440,140",
            "-stroke", accent2, "-strokewidth", "2",
            "-draw", "circle 1440,540 1440,260",
            "-draw", "line 1040,540 1840,540",
            "-channel", "A", "-evaluate", "multiply", a_alpha, "+channel",
            "-resize", "3840x2160!", ")",
            "-compose", "over", "-composite",
        ]
    if role == "SENTINEL":
        return [
            "(", "-size", "1920x1080", "xc:none",
            "-fill", "none", "-stroke", accent, "-strokewidth", "2",
            "-draw", "line 1060,96 1060,984",
            "-draw", "line 1820,96 1820,984",
            "-draw", "line 1030,130 1110,130",
            "-draw", "line 1030,950 1110,950",
            "-stroke", accent2, "-strokewidth", "2",
            "-draw", "line 1770,130 1850,130",
            "-draw", "line 1770,950 1850,950",
            "-draw", "rectangle 1080,150 1800,930",
            "-channel", "A", "-evaluate", "multiply", b_alpha, "+channel",
            "-resize", "3840x2160!", ")",
            "-compose", "over", "-composite",
        ]
    # INITIATOR
    return [
        "(", "-size", "1920x1080", "xc:none",
        "-fill", "none", "-stroke", accent, "-strokewidth", "3",
        "-draw", "arc 1020,120 1860,960 200,340",
        "-draw", "arc 1120,220 1760,860 15,155",
        "-stroke", accent2, "-strokewidth", "2",
        "-draw", "line 960,540 1240,540",
        "-draw", "line 1640,540 1880,540",
        "-channel", "A", "-evaluate", "multiply", a_alpha, "+channel",
        "-resize", "3840x2160!", ")",
        "-compose", "over", "-composite",
    ]


def signature_wallpaper(agent: dict, pal: dict[str, str], clean: bool, dst: Path) -> None:
    """Composite a 3840x2160 wallpaper from the official agent render."""
    slug = agent["slug"]
    portrait = PORTRAITS / f"{slug}.png"
    if not portrait.exists():
        raise SystemExit(f"missing portrait for {slug}: {portrait}")

    light_mode = pal["mode"] == "light"
    accent = pal["accent"]
    accent2 = pal["icon_mark"]
    bg = pal["background"]
    fg = pal["foreground"]
    muted = pal["dark_foreground"]

    name = agent["name"].upper()
    role = agent["role"].upper()
    origin = agent["origin"]
    sig = agent["signature"].upper()
    ult = agent["ultimate"].upper()
    num = agent["number"]

    work = Path("/tmp/opencode")
    work.mkdir(parents=True, exist_ok=True)
    base = work / f"vt-{slug}-base.png"
    halo = work / f"vt-{slug}-halo.png"
    glow2 = work / f"vt-{slug}-glow2.png"
    watermark = work / f"vt-{slug}-wm.png"

    a1_alpha = "40" if light_mode else "66"
    a2_alpha = "2E" if light_mode else "44"

    # Base: asymmetric dual-tone studio bloom (accent behind agent, accent2 lower-left).
    run([
        "magick", "-size", "960x540", f"xc:{bg}",
        "(", "-size", "900x900", f"radial-gradient:{accent}{a1_alpha}-{accent}00", ")",
        "-gravity", "northwest", "-geometry", "+260-150", "-compose", "over", "-composite",
        "(", "-size", "820x820", f"radial-gradient:{accent2}{a2_alpha}-{accent2}00", ")",
        "-gravity", "northwest", "-geometry", "-220+110", "-compose", "over", "-composite",
        "-resize", "3840x2160!", str(base),
    ])

    # Halo behind portrait.
    halo_alpha = "0.22" if light_mode else "0.34"
    run([
        "magick", "-size", "1100x1100", "xc:none", "-fill", accent,
        "-draw", "circle 550,550 550,120", "-blur", "0x110",
        "-channel", "A", "-evaluate", "multiply", halo_alpha, "+channel",
        "-resize", "1950x1950", str(halo),
    ])

    # Secondary accent rim bloom at bottom-right.
    rim_alpha = "0.14" if light_mode else "0.22"
    run([
        "magick", "-size", "800x800", "xc:none", "-fill", accent2,
        "-draw", "circle 400,400 400,110", "-blur", "0x90",
        "-channel", "A", "-evaluate", "multiply", rim_alpha, "+channel",
        "-resize", "1400x1400", str(glow2),
    ])

    cmd = ["magick", str(base)]
    if not clean:
        cmd += role_motif_commands(role, accent, accent2, light_mode)
        # Subtle architectural watermark behind the agent.
        wm_color = mix(bg, accent, 0.22 if light_mode else 0.16)
        run([
            "magick", "-background", "none", "-fill", wm_color,
            "-font", str(FONT_BEBAS), "-pointsize", "520",
            f"label:{name}", "-trim", "+repage", str(watermark),
        ])
        cmd += [str(watermark), "-gravity", "west", "-geometry", "+1120+80",
                "-compose", "over", "-composite"]

    cmd += [
        "-gravity", "northwest",
        str(halo), "-geometry", "+2180+220", "-compose", "over", "-composite",
        str(glow2), "-geometry", "+2480+820", "-compose", "over", "-composite",
        "(", str(portrait), "-filter", "Lanczos", "-trim", "+repage",
        "-resize", "x2040", ")",
        "-gravity", "northeast", "-geometry", "+80+120",
        "-compose", "over", "-composite",
    ]

    if not clean:
        def label(text: str, font: Path, pointsize: int, fill: str, tag: str) -> Path:
            p = work / f"vt-{slug}-{tag}.png"
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

        # Window-safe corner HUD: fits cleanly above (y<190) and below (y>1955)
        # standard Omarchy/Hyprland tiled windows while framing empty desktops.
        eyebrow = label(f"// VALORANT PROTOCOL  ·  AGENT {num}", FONT_RAJ_SB, 22, accent, "eyebrow")
        name_img = label(name, FONT_BEBAS, 86, fg, "name")
        nw, nh = size(name_img)
        if nw > 560:
            run(["magick", str(name_img), "-resize", "560x", "-filter", "Lanczos", "+repage", str(name_img)])
            nw, nh = size(name_img)
        role_img = label(f"{role}  //  {origin}", FONT_RAJ_B, 28, accent2, "role")
        _, rh = size(role_img)

        sig_label = label("SIGNATURE", FONT_RAJ_SB, 20, muted, "sig-label")
        sig_img = label(sig, FONT_BEBAS, 56, fg, "sig")
        sw, _ = size(sig_img)
        ult_label = label("ULTIMATE", FONT_RAJ_SB, 20, muted, "ult-label")
        ult_img = label(ult, FONT_BEBAS, 56, accent2, "ult")
        footer = label("VALORANT  //  OMARCHY AGENT THEMES", FONT_RAJ_M, 20, muted, "footer")

        name_y = 104
        role_y = name_y + nh - rh - 4
        role_x = 110 + nw + 28
        rule_y = name_y + nh + 12
        ult_x = max(360, 110 + sw + 72)

        cmd += ["-gravity", "northwest", "-compose", "over"]
        for img, x, y in (
            (eyebrow, 110, 72),
            (name_img, 108, name_y),
            (role_img, role_x, role_y),
            (sig_label, 110, 1958),
            (sig_img, 108, 1984),
            (ult_label, ult_x, 1958),
            (ult_img, ult_x - 2, 1984),
            (footer, 110, 2070),
        ):
            cmd += [str(img), "-geometry", f"+{x}+{y}", "-composite"]
        cmd += [
            "-fill", accent, "-draw", f"rectangle 110,{rule_y} 290,{rule_y + 4}",
            "-fill", accent2, "-draw", f"rectangle 298,{rule_y} 380,{rule_y + 4}",
        ]

    cmd += ["-quality", "92", "-define", "webp:method=6", str(dst)]
    run(cmd)


def build_walls(agent: dict, pal: dict[str, str], only_generated: bool = False) -> None:
    theme = THEMES / f"valorant-{agent['slug']}"
    bgdir = theme / "backgrounds"
    bgdir.mkdir(parents=True, exist_ok=True)

    # Always refresh the signature wallpaper.
    signature_wallpaper(agent, pal, clean=False, dst=bgdir / f"0-{agent['slug']}-signature.webp")

    if only_generated:
        return

    if SOURCE_WALLS.exists() and agent["sources"]:
        for old in bgdir.glob("*"):
            if old.name != f"0-{agent['slug']}-signature.webp":
                old.unlink()
        index = 1
        for original in agent["sources"]:
            src = SOURCE_WALLS / original
            if not src.exists():
                print(f"  ! missing wallpaper {src}", file=sys.stderr)
                continue
            stem = original.rsplit(".", 1)[0].replace("\\", "").replace(" ", "-")
            dst = bgdir / f"{index}-{stem}.webp"
            export_wallpaper(src, dst)
            index += 1
        return

    # Preserve curated wallpapers already committed in the repo; only build the
    # clean companion wallpaper when an agent has no extra wallpapers.
    extras = [p for p in bgdir.iterdir()
              if p.is_file() and p.name not in (
                  f"0-{agent['slug']}-signature.webp",
                  f"1-{agent['slug']}-clean.webp",
              )]
    if not extras:
        signature_wallpaper(agent, pal, clean=True, dst=bgdir / f"1-{agent['slug']}-clean.webp")


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
        pal = write_colors(slug, accent, accent2, bg)
        theme = THEMES / f"valorant-{slug}"
        (theme / "icons.theme").write_text(icon + "\n", encoding="utf-8")
        if not args.no_walls:
            build_walls(
                {
                    "slug": slug, "name": name, "role": role, "origin": origin,
                    "number": number, "signature": sig, "ultimate": ult,
                    "accent": pal["accent"], "accent2": pal["icon_mark"],
                    "background": bg, "sources": sources,
                },
                pal,
                only_generated=args.generated_walls_only,
            )
        manifest.append({
            "slug": slug,
            "theme": f"valorant-{slug}",
            "name": name,
            "role": role,
            "origin": origin,
            "number": number,
            "mode": pal["mode"],
            "signature": sig,
            "ultimate": ult,
            "accent": pal["accent"],
            "accent2": pal["icon_mark"],
            "background": bg,
        })

    if not args.only:
        (ROOT / "agents.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    print(f"built {len(manifest)} theme(s)")


if __name__ == "__main__":
    main()

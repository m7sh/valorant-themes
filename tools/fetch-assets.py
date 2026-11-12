#!/usr/bin/env python3
"""Refresh the assets used by tools/build.py.

Downloads the official agent renders from valorant-api.com and the two OFL
fonts from the google/fonts repository. Run this before a full rebuild on a
fresh clone, or when a new agent is added to tools/build.py.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORTRAITS = ROOT / "assets" / "portraits"
FONTS = ROOT / "assets" / "fonts"

FONT_URLS = {
    "BebasNeue-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
    "Rajdhani-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/rajdhani/Rajdhani-Bold.ttf",
    "Rajdhani-SemiBold.ttf": "https://github.com/google/fonts/raw/main/ofl/rajdhani/Rajdhani-SemiBold.ttf",
    "Rajdhani-Medium.ttf": "https://github.com/google/fonts/raw/main/ofl/rajdhani/Rajdhani-Medium.ttf",
}


def fetch(url: str, destination: Path) -> None:
    if destination.exists():
        print(f"have   {destination.relative_to(ROOT)}")
        return
    print(f"fetch  {destination.relative_to(ROOT)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, destination)


def main() -> None:
    PORTRAITS.mkdir(parents=True, exist_ok=True)
    FONTS.mkdir(parents=True, exist_ok=True)

    for name, url in FONT_URLS.items():
        fetch(url, FONTS / name)

    with urllib.request.urlopen("https://valorant-api.com/v1/agents?isPlayableCharacter=true") as response:
        agents = json.load(response)["data"]

    for agent in sorted(agents, key=lambda a: a["displayName"]):
        slug = "".join(ch for ch in agent["displayName"].lower() if ch.isalnum())
        fetch(agent["fullPortrait"], PORTRAITS / f"{slug}.png")

    print(f"\n{len(agents)} agent renders ready in assets/portraits/")


if __name__ == "__main__":
    sys.exit(main())

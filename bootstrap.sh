#!/usr/bin/env bash
# One-command installer for the VALORANT Agent Themes bundle.
#
#   curl -fsSL https://raw.githubusercontent.com/m7sh/valorant-themes/main/bootstrap.sh | bash
#   curl -fsSL .../bootstrap.sh | bash -s -- jett
#   curl -fsSL .../bootstrap.sh | bash -s -- --list
set -euo pipefail

REPO_URL="${VALORANT_THEMES_REPO:-https://github.com/m7sh/valorant-themes.git}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/valorant-themes"

if [[ -d $DATA_DIR/.git ]]; then
  printf 'Updating %s\n' "$DATA_DIR"
  git -C "$DATA_DIR" pull --ff-only
else
  printf 'Cloning %s\n' "$REPO_URL"
  mkdir -p "$(dirname -- "$DATA_DIR")"
  git clone --depth 1 "$REPO_URL" "$DATA_DIR"
fi

exec "$DATA_DIR/install.sh" "$@"

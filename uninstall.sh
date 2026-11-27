#!/usr/bin/env bash
# VALORANT Agent Themes for Omarchy
# Uninstall one, several, or every agent theme.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
VALORANT Agent Themes for Omarchy — Uninstall

Usage:
  ./uninstall.sh                     Remove every valorant-* theme
  ./uninstall.sh all                 Remove every valorant-* theme
  ./uninstall.sh jett                Remove one theme
  ./uninstall.sh jett reyna viper    Remove several themes

Options:
  -l, --list        List all agent themes
      --dry-run     Show what would happen
  -h, --help        Show this help

Agent names are case-insensitive. `jett`, `Jett` and `valorant-jett` all work.
EOF
}

for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
  esac
done

exec "$ROOT/install.sh" --remove "$@"

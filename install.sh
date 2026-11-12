#!/usr/bin/env bash
# VALORANT Agent Themes for Omarchy
# Install one, several, or every agent theme.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
THEMES_DIR="$ROOT/themes"
DEST="${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/themes"
MANIFEST="$ROOT/agents.json"

MODE=install
LINK=0
FORCE=0
SET_THEME=0
DRY_RUN=0
SELECTED=()

usage() {
  cat <<'EOF'
VALORANT Agent Themes for Omarchy

Usage:
  ./install.sh                     Install every agent theme
  ./install.sh all                 Install every agent theme
  ./install.sh jett                Install one theme
  ./install.sh jett reyna viper    Install several themes
  ./install.sh --list              List agents and their abilities
  ./install.sh --link jett         Symlink instead of copy (repo stays live)
  ./install.sh --remove jett       Remove one theme
  ./install.sh --remove all        Remove every valorant-* theme
  ./install.sh --set jett          Install and apply the theme

Options:
  -l, --list        List all agent themes
  -r, --remove      Remove the selected themes
      --link        Symlink theme folders into ~/.config/omarchy/themes
      --set         Apply the first installed theme with `omarchy theme set`
      --force       Overwrite an existing theme (copy mode)
      --dry-run     Show what would happen
  -h, --help        Show this help

Agent names are case-insensitive. `jett`, `Jett` and `valorant-jett` all work.
EOF
}

die() { printf 'error: %s\n' "$*" >&2; exit 1; }

normalize() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/^valorant[-_ ]*//; s/[^a-z0-9]//g'
}

all_slugs() {
  if [[ -f $MANIFEST ]] && command -v python3 >/dev/null 2>&1; then
    python3 - "$MANIFEST" <<'PY'
import json, sys
for agent in json.load(open(sys.argv[1])):
    print(agent["slug"])
PY
  else
    find "$THEMES_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' |
      sed 's/^valorant-//' | sort
  fi
}

list_agents() {
  if [[ -f $MANIFEST ]] && command -v python3 >/dev/null 2>&1; then
    python3 - "$MANIFEST" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1]))
head = f"{'THEME':<22} {'AGENT':<12} {'ROLE':<11} {'SIGNATURE':<20} ULTIMATE"
print(head)
print("-" * len(head))
for a in rows:
    print(f"{a['theme']:<22} {a['name']:<12} {a['role']:<11} {a['signature']:<20} {a['ultimate']}")
PY
  else
    find "$THEMES_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort
  fi
}

resolve() {
  local wanted slug
  wanted="$(normalize "$1")"
  for slug in $(all_slugs); do
    [[ "$wanted" == "$slug" ]] && { printf '%s' "$slug"; return 0; }
  done
  # Friendly aliases that are not just the slug.
  case "$wanted" in
    kj) printf '%s' "killjoy"; return 0 ;;
    brim|brimmy) printf '%s' "brimstone"; return 0 ;;
  esac
  return 1
}

while (($#)); do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -l|--list) list_agents; exit 0 ;;
    -r|--remove) MODE=remove; shift ;;
    --link) LINK=1; shift ;;
    --set) SET_THEME=1; shift ;;
    --force) FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    all) SELECTED+=("__all__"); shift ;;
    -*) die "unknown option: $1 (try --help)" ;;
    *)
      slug="$(resolve "$1")" || die "unknown agent '$1'. Run ./install.sh --list"
      SELECTED+=("$slug")
      shift
      ;;
  esac
done

if [[ ${#SELECTED[@]} -eq 0 ]]; then
  SELECTED=("__all__")
elif [[ " ${SELECTED[*]} " == *" __all__ "* ]]; then
  SELECTED=("__all__")
fi

# Expand "all" and de-duplicate while preserving order.
FINAL=()
if [[ ${SELECTED[0]} == "__all__" ]]; then
  while IFS= read -r slug; do FINAL+=("$slug"); done < <(all_slugs)
else
  declare -A seen=()
  for slug in "${SELECTED[@]}"; do
    [[ -n ${seen[$slug]:-} ]] && continue
    seen[$slug]=1
    FINAL+=("$slug")
  done
fi

[[ ${#FINAL[@]} -gt 0 ]] || die "no themes selected"

if [[ $MODE == install ]]; then
  mkdir -p "$DEST"
  installed=()
  for slug in "${FINAL[@]}"; do
    src="$THEMES_DIR/valorant-$slug"
    dst="$DEST/valorant-$slug"
    [[ -d $src ]] || die "theme directory missing: $src"

    if [[ $DRY_RUN -eq 1 ]]; then
      printf 'would install %s -> %s\n' "$src" "$dst"
      continue
    fi

    if [[ -e $dst || -L $dst ]]; then
      if [[ $FORCE -eq 0 && $LINK -eq 0 ]]; then
        printf 'skip   %s (already installed, use --force)\n' "valorant-$slug"
        installed+=("$slug")
        continue
      fi
      rm -rf "$dst"
    fi

    if [[ $LINK -eq 1 ]]; then
      ln -s "$src" "$dst"
      printf 'linked %s -> %s\n' "valorant-$slug" "$src"
    else
      cp -a "$src" "$dst"
      printf 'install %s\n' "valorant-$slug"
    fi
    installed+=("$slug")
  done

  if [[ $SET_THEME -eq 1 && ${#installed[@]} -gt 0 && $DRY_RUN -eq 0 ]]; then
    if command -v omarchy >/dev/null 2>&1; then
      omarchy theme set "valorant-${installed[0]}"
    else
      printf 'note: omarchy not on PATH; run: omarchy theme set valorant-%s\n' "${installed[0]}"
    fi
  fi

  if [[ $DRY_RUN -eq 0 ]]; then
    printf '\nInstalled %d theme(s) in %s\n' "${#installed[@]}" "$DEST"
    printf 'Apply one with:  omarchy theme set valorant-%s\n' "${installed[0]}"
  fi
else
  for slug in "${FINAL[@]}"; do
    dst="$DEST/valorant-$slug"
    if [[ -e $dst || -L $dst ]]; then
      if [[ $DRY_RUN -eq 1 ]]; then
        printf 'would remove %s\n' "$dst"
      else
        rm -rf "$dst"
        printf 'removed %s\n' "valorant-$slug"
      fi
    else
      printf 'not installed: valorant-%s\n' "$slug"
    fi
  done
fi

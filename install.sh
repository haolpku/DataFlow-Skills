#!/usr/bin/env bash
#
# DataFlow-Skills installer
#
# Usage:
#   ./install.sh                                # install all skills to ~/.claude/skills/
#   ./install.sh --project                      # install to ./.claude/skills/ (current project)
#   ./install.sh dataflow-dev                   # install only the named skill(s)
#   ./install.sh --project core_text generating-dataflow-pipeline
#   ./install.sh --force                        # overwrite existing skill dirs
#   ./install.sh --help
#
# Behavior:
#   - copies each requested skill directory into the target location
#   - skips skills that already exist unless --force is passed
#   - verifies SKILL.md exists at the destination after copying
#   - exits non-zero if any requested skill fails to install or verify
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# All shippable skill directories in this repo.
ALL_SKILLS=(
  core_text
  generating-dataflow-pipeline
  dataflow-dev
)

usage() {
  sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
}

target_root="$HOME/.claude/skills"
force=0
selected=()

# --- parse arguments ------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      target_root="$(pwd)/.claude/skills"
      shift
      ;;
    --user)
      target_root="$HOME/.claude/skills"
      shift
      ;;
    --force|-f)
      force=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      selected+=("$1")
      shift
      ;;
  esac
done

# Default to all skills if nothing was named on the CLI.
if [[ ${#selected[@]} -eq 0 ]]; then
  selected=("${ALL_SKILLS[@]}")
fi

# --- validate skill names -------------------------------------------------
for name in "${selected[@]}"; do
  found=0
  for known in "${ALL_SKILLS[@]}"; do
    if [[ "$name" == "$known" ]]; then
      found=1
      break
    fi
  done
  if [[ $found -eq 0 ]]; then
    echo "[error] unknown skill: $name" >&2
    echo "        available: ${ALL_SKILLS[*]}" >&2
    exit 2
  fi
  if [[ ! -f "$REPO_ROOT/$name/SKILL.md" ]]; then
    echo "[error] $REPO_ROOT/$name/SKILL.md not found — is the repo intact?" >&2
    exit 1
  fi
done

# --- install --------------------------------------------------------------
mkdir -p "$target_root"
echo "Installing into: $target_root"
echo

failed=()
for name in "${selected[@]}"; do
  src="$REPO_ROOT/$name"
  dst="$target_root/$name"

  if [[ -e "$dst" ]]; then
    if [[ $force -eq 1 ]]; then
      echo "[overwrite] $name"
      rm -rf "$dst"
    else
      echo "[skip] $name already exists at $dst (use --force to overwrite)"
      continue
    fi
  else
    echo "[install]   $name"
  fi

  cp -R "$src" "$dst"

  # Verify
  if [[ ! -f "$dst/SKILL.md" ]]; then
    echo "[error]     $name: SKILL.md missing at $dst after copy" >&2
    failed+=("$name")
  fi
done

echo
if [[ ${#failed[@]} -gt 0 ]]; then
  echo "Failed: ${failed[*]}" >&2
  exit 1
fi

echo "Done. In Claude Code, type one of:"
for name in "${selected[@]}"; do
  echo "  /$name"
done

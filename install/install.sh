#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash install/install.sh <codex|claude> [--dest PATH] [--copy] [--force] [skill ...]

Examples:
  bash install/install.sh codex
  bash install/install.sh claude analyzing-stocks analyzing-banks
  bash install/install.sh codex --dest "$HOME/.agents/skills" --copy analyzing-stocks
EOF
}

die() {
  echo "Error: $*" >&2
  exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_ROOT="$REPO_ROOT/skills"

[[ $# -ge 1 ]] || {
  usage
  exit 1
}

PLATFORM="$1"
shift

case "$PLATFORM" in
  codex)
    DEST_DIR="${HOME}/.agents/skills"
    ;;
  claude)
    DEST_DIR="${HOME}/.claude/skills"
    ;;
  -h|--help|help)
    usage
    exit 0
    ;;
  *)
    die "unknown platform: $PLATFORM"
    ;;
esac

MODE="symlink"
FORCE=0
declare -a REQUESTED_SKILLS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      [[ $# -ge 2 ]] || die "--dest requires a path"
      DEST_DIR="$2"
      shift 2
      ;;
    --copy)
      MODE="copy"
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      REQUESTED_SKILLS+=("$1")
      shift
      ;;
  esac
done

[[ -d "$SKILLS_ROOT" ]] || die "skills directory not found: $SKILLS_ROOT"
mkdir -p "$DEST_DIR"

if [[ ${#REQUESTED_SKILLS[@]} -eq 0 ]]; then
  while IFS= read -r skill_path; do
    REQUESTED_SKILLS+=("$(basename "$skill_path")")
  done < <(find "$SKILLS_ROOT" -mindepth 1 -maxdepth 1 -type d | sort)
fi

for skill in "${REQUESTED_SKILLS[@]}"; do
  SOURCE_PATH="$SKILLS_ROOT/$skill"
  TARGET_PATH="$DEST_DIR/$skill"

  [[ -d "$SOURCE_PATH" ]] || die "skill not found: $skill"

  if [[ -e "$TARGET_PATH" || -L "$TARGET_PATH" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
      rm -rf "$TARGET_PATH"
    else
      die "target already exists: $TARGET_PATH (use --force to replace it)"
    fi
  fi

  if [[ "$MODE" == "copy" ]]; then
    cp -R "$SOURCE_PATH" "$TARGET_PATH"
  else
    ln -s "$SOURCE_PATH" "$TARGET_PATH"
  fi

  echo "installed $skill -> $TARGET_PATH"
done

echo "installation complete for platform: $PLATFORM"

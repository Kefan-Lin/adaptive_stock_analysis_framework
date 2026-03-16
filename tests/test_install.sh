#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_exists() {
  local path="$1"
  [[ -e "$path" ]] || fail "expected path to exist: $path"
}

assert_not_exists() {
  local path="$1"
  [[ ! -e "$path" ]] || fail "expected path to be absent: $path"
}

assert_symlink_target() {
  local path="$1"
  local expected="$2"
  [[ -L "$path" ]] || fail "expected symlink: $path"
  local actual
  actual="$(python3 -c 'import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve())' "$path")"
  [[ "$actual" == "$expected" ]] || fail "symlink target mismatch: $path -> $actual (expected $expected)"
}

assert_not_symlink() {
  local path="$1"
  [[ ! -L "$path" ]] || fail "expected regular directory, got symlink: $path"
}

CODEx_DEST="$TMP_DIR/codex-skills"
CLAUDE_DEST="$TMP_DIR/claude-skills"
COPY_DEST="$TMP_DIR/copied-skills"

bash "$REPO_ROOT/install/install-codex.sh" --dest "$CODEx_DEST"
assert_symlink_target "$CODEx_DEST/analyzing-stocks" "$REPO_ROOT/skills/analyzing-stocks"
assert_symlink_target "$CODEx_DEST/analyzing-banks" "$REPO_ROOT/skills/analyzing-banks"
assert_symlink_target "$CODEx_DEST/analyzing-utilities-telecom" "$REPO_ROOT/skills/analyzing-utilities-telecom"

bash "$REPO_ROOT/install/install-claude.sh" --dest "$CLAUDE_DEST" analyzing-stocks analyzing-software-platforms
assert_symlink_target "$CLAUDE_DEST/analyzing-stocks" "$REPO_ROOT/skills/analyzing-stocks"
assert_symlink_target "$CLAUDE_DEST/analyzing-software-platforms" "$REPO_ROOT/skills/analyzing-software-platforms"
assert_not_exists "$CLAUDE_DEST/analyzing-banks"

bash "$REPO_ROOT/install/install.sh" codex --dest "$COPY_DEST" --copy analyzing-stocks
assert_exists "$COPY_DEST/analyzing-stocks/SKILL.md"
assert_not_symlink "$COPY_DEST/analyzing-stocks"

echo "install tests passed"

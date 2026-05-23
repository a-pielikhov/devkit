#!/usr/bin/env bash
# dev.sh — start a local devkit development shell.
#
# Usage:  ./dev.sh   (exit or Ctrl+D to leave)

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO/.venv"
DEVKIT="$VENV/bin/devkit"

# ── 1. Sync workspace ────────────────────────────────────────────────────────
printf '→ syncing workspace… '
uv sync --quiet --project "$REPO"
echo "ok"

# ── 2. Tab completion ────────────────────────────────────────────────────────
if "$DEVKIT" --install-completion zsh &>/dev/null; then
  echo "→ tab completion: installed"
else
  echo "→ tab completion: already up to date"
fi

# ── 3. Launch dev shell ──────────────────────────────────────────────────────
# Use ZDOTDIR so our PATH override runs AFTER ~/.zshrc (which prepends its own
# entries and would otherwise push the venv out of first position).
ZDOTDIR_TMP="$(mktemp -d)"
cat > "$ZDOTDIR_TMP/.zshrc" << ZSHRC
[[ -f "\$HOME/.zshrc" ]] && source "\$HOME/.zshrc"
# Override any devkit shell function defined in ~/.zshrc so the dev venv always wins.
devkit() { "$DEVKIT" "\$@"; }
export PATH="$VENV/bin:\$PATH"
export VIRTUAL_ENV="$VENV"
ZSHRC

echo ""
echo "  devkit dev shell  ·  local source"
echo "  $(ZDOTDIR="$ZDOTDIR_TMP" "$VENV/bin/python" -c 'import importlib.metadata; print("v" + importlib.metadata.version("devkit-core"))')"
echo "  binary: $DEVKIT"
echo "  edits to devkit-*/src/ are live — no rebuild needed"
echo "  type 'exit' or Ctrl+D to leave"
echo ""

# Run as subshell (no exec) so bash stays alive for terminal session tracking.
ZDOTDIR="$ZDOTDIR_TMP" zsh -i
STATUS=$?

rm -rf "$ZDOTDIR_TMP"
exit $STATUS

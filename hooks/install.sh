#!/bin/bash
# Install hooks into ~/.claude/hooks/
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.claude/hooks"
mkdir -p "$DEST"
cp "$SCRIPT_DIR/session-end-extract.py" "$DEST/"
cp "$SCRIPT_DIR/consolidation-check.sh" "$DEST/"
chmod +x "$DEST/session-end-extract.py" "$DEST/consolidation-check.sh"
echo "Installed hooks to $DEST"
echo "Add SessionStart and SessionEnd entries to ~/.claude/settings.json manually."

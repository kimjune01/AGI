#!/bin/bash
# Install consolidation hooks into ~/.claude/
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
HARNESS_DIR="$REPO_DIR/harness"
DEST="$HOME/.claude/hooks"
MEMORY="$HOME/.claude/memory"
SETTINGS="$HOME/.claude/settings.json"

# Create directories
mkdir -p "$DEST" "$MEMORY/actions"

# Copy hooks
cp "$SCRIPT_DIR/session-end-extract.py" "$DEST/"
cp "$SCRIPT_DIR/consolidation-check.sh" "$DEST/"
chmod +x "$DEST/session-end-extract.py" "$DEST/consolidation-check.sh"

# Write harness path so hooks can find the repo
echo "$HARNESS_DIR" > "$MEMORY/harness_path"

# Initialize config if missing
[ -f "$MEMORY/config.json" ] || echo '{"turn_threshold": 1000, "min_coactivation": 3}' > "$MEMORY/config.json"
[ -f "$MEMORY/turn_counter.json" ] || echo "{\"count\": 0, \"last_reset\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$MEMORY/turn_counter.json"

# Patch settings.json
if [ -f "$SETTINGS" ]; then
    python3 -c "
import json, sys
with open('$SETTINGS') as f:
    s = json.load(f)
hooks = s.setdefault('hooks', {})
# Add SessionEnd if missing
if 'SessionEnd' not in hooks:
    hooks['SessionEnd'] = [{'hooks': [{'type': 'command', 'command': 'python3 ~/.claude/hooks/session-end-extract.py'}]}]
# Add SessionStart if missing
if 'SessionStart' not in hooks:
    hooks['SessionStart'] = [{'hooks': [{'type': 'command', 'command': 'bash ~/.claude/hooks/consolidation-check.sh'}]}]
with open('$SETTINGS', 'w') as f:
    json.dump(s, f, indent=2)
    f.write('\n')
print('Patched $SETTINGS')
"
else
    python3 -c "
import json
s = {'hooks': {
    'SessionStart': [{'hooks': [{'type': 'command', 'command': 'bash ~/.claude/hooks/consolidation-check.sh'}]}],
    'SessionEnd': [{'hooks': [{'type': 'command', 'command': 'python3 ~/.claude/hooks/session-end-extract.py'}]}],
}}
with open('$SETTINGS', 'w') as f:
    json.dump(s, f, indent=2)
    f.write('\n')
print('Created $SETTINGS')
"
fi

echo "Installed hooks to $DEST"
echo "Harness path: $HARNESS_DIR"
echo ""
echo "Next steps:"
echo "  cd $HARNESS_DIR && uv run python backfill.py   # index existing transcripts"
echo "  # Then just use Claude Code normally. The hooks handle the rest."

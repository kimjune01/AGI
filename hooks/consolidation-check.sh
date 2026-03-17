#!/bin/bash
# SessionStart hook: notify if consolidation is due
MARKER="$HOME/.claude/memory/consolidation-due"
HARNESS_PATH_FILE="$HOME/.claude/memory/harness_path"

if [ -f "$MARKER" ]; then
    count=$(python3 -c "import json; print(json.load(open('$HOME/.claude/memory/turn_counter.json')).get('count', 0))" 2>/dev/null || echo "?")
    harness=$(cat "$HARNESS_PATH_FILE" 2>/dev/null || echo "~/Documents/agi/harness")
    cat <<EOF
[Consolidation due] $count turns accumulated since last reset.
When the user is ready, run the consolidation pipeline:
  cd $harness && uv run python run_pipeline.py
Then remove the marker: rm ~/.claude/memory/consolidation-due
And reset the counter in ~/.claude/memory/turn_counter.json to 0.
EOF
fi

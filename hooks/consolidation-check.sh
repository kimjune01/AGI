#!/bin/bash
# SessionStart hook: notify if consolidation is due
MARKER="$HOME/.claude/memory/consolidation-due"
if [ -f "$MARKER" ]; then
    count=$(python3 -c "import json; print(json.load(open('$HOME/.claude/memory/turn_counter.json')).get('count', 0))" 2>/dev/null || echo "?")
    cat <<EOF
[Consolidation due] $count turns accumulated since last reset.
When the user is ready, run the consolidation pipeline:
  cd ~/Documents/agi/harness && uv run python -m run_pipeline
Then remove the marker: rm ~/.claude/memory/consolidation-due
And reset the counter in ~/.claude/memory/turn_counter.json to 0.
EOF
fi

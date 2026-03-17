# AGI Consolidation Harness

A self-improving loop for Claude Code. Watches sessions, extracts action patterns, surfaces repeating workflows that should become skills.

## When the user says "set up the consolidation harness"

Run these commands in order:

```bash
bash hooks/install.sh
cd harness && uv run python backfill.py
```

Then confirm: hooks are installed, transcripts are indexed, the harness is live.

## When the user says "run consolidation"

```bash
cd harness && uv run python run_pipeline.py
```

Then show the user the top patterns and ask which ones to promote to skills. After review:

```bash
rm ~/.claude/memory/consolidation-due
```

And reset the counter:

```bash
python3 -c "import json; json.dump({'count': 0, 'last_reset': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}, open(__import__('os').path.expanduser('~/.claude/memory/turn_counter.json'), 'w'))"
```

## How it works

1. **SessionEnd hook** extracts action records from every transcript into `~/.claude/memory/actions/`
2. **Turn counter** accumulates. At 1,000 turns, touches a marker file.
3. **SessionStart hook** sees the marker and prompts to run consolidation.
4. **Pipeline** finds repeating workflows and proposes skills.

## Running tests

```bash
cd harness && uv run --group dev pytest -v
```

## Dependencies

- Python 3.9+ (stdlib only, no pip packages)
- `uv` for running harness scripts
- Claude Code with hooks support

## File layout

- `hooks/` — installable hook scripts + install.sh
- `harness/` — pipeline code (extract, perceive, cluster, filter, propose)
- `corpus/` — test posts for skill mutation experiments
- `variants/` — skill mutation candidates
- `results/` — experiment logs

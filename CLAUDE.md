# AGI Consolidation Harness

## What this is

A self-improving loop for Claude Code. It watches your sessions, extracts action patterns, and surfaces repeating workflows that should become skills.

## Setup (run once)

```bash
bash hooks/install.sh
cd harness && uv run python backfill.py
```

That's it. The hooks fire automatically on every session start and end.

## How it works

1. **SessionEnd hook** extracts action records from every transcript into `~/.claude/memory/actions/`
2. **Turn counter** accumulates. At 1,000 turns, touches a marker file.
3. **SessionStart hook** sees the marker and prompts you to run consolidation.
4. **Pipeline** (`cd harness && uv run python run_pipeline.py`) finds repeating workflows and proposes skills.

## Running tests

```bash
cd harness && uv run --group dev pytest -v
```

## Running the pipeline manually

```bash
cd harness && uv run python run_pipeline.py
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

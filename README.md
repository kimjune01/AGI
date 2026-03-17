# AGI

Skill consolidation harness. The experiment that closes the loop.

## Thesis

Claude Code has `create-skill`: the only procedure that writes procedures. That's the Consolidate cell. Dimmed because the agent never initiates. This harness makes it automatic.

Track which action sequences repeat with user approval across sessions. When a pattern recurs above threshold, condense it into a skill. Score against a mutation. Winner survives. Two iterations to convergence.

Three agents, three roles:
- **Codex (GPT-5.4)** — scores skill variants against the contract. The A/B test harness.
- **Claude Code** — creates and mutates skills. The skill mutator.
- **Human** — approves or rejects consolidated skills. The Attend.

## Architecture

```
hooks/
├── session-end-extract.py    # SessionEnd: transcript → action records
├── consolidation-check.sh    # SessionStart: prompt when consolidation due
└── install.sh                # copies hooks to ~/.claude/hooks/

harness/
├── extract.py                # parse JSONL transcript → action records
├── perceive.py               # intent-first clustering (TF-IDF on prompts)
├── cluster.py                # group similar patterns (Jaccard + edit distance)
├── filter.py                 # reject homogeneous, below-threshold
├── propose.py                # format candidate as draft SKILL.md
├── run_pipeline.py           # one-command full pipeline run
├── backfill.py               # one-shot: extract all existing transcripts
├── config.py                 # path constants, thresholds
├── test_extract.py           # 18 tests
└── test_perceive.py          # 18 tests

~/.claude/memory/
├── actions/                  # one JSONL per session (action records)
├── config.json               # turn_threshold (1000), min_coactivation (3)
├── turn_counter.json         # accumulator, triggers consolidation
└── consolidation-due         # zero-byte marker (presence = signal)
```

## The loop

```
SessionEnd hook fires
    │
    ▼
extract.py → ~/.claude/memory/actions/{session_id}.jsonl
    │
    └─► turn_counter.json += turns
            │
            ├─ counter < 1000 → done
            └─ counter >= 1000 → touch consolidation-due
                                    │
                                    ▼
                    SessionStart hook sees marker
                    prompts Claude to run pipeline
                                    │
                                    ▼
1. PERCEIVE     perceive.py — cluster by intent (TF-IDF on prompts)
2. FILTER       filter.py   — reject homogeneous, below-threshold
3. ATTEND       human reviews candidates.md
4. CONSOLIDATE  propose.py → write winning pattern as SKILL.md
5. REMEMBER     skill persists in ~/.claude/skills/
```

## Experiment 1: Humanize mutation

The first skill to evolve. `humanize` has a well-defined contract:
- Input: a blog post
- Output: list of AI patterns found + opportunities for voice
- Verifiable: did the fix improve the prose?

### Protocol

1. Read current `humanize/SKILL.md`
2. Codex proposes one mutation (add a pattern, remove a pattern, change a threshold)
3. Run both variants on the same test post
4. Codex scores: which output better satisfies the contract?
5. Winner replaces the skill. Loser is logged.
6. Repeat until convergence (expected: 2 iterations per the [slop-detection result](https://www.june.kim/slop-detection))

### Result

Round 1 ([001](results/001-disposable-analogies.md)): mutation too narrow, no recall gain. A wins on parsimony.

## Experiment 2: Session logging harness

Backfilled 446 transcripts → 13,427 action records. First pipeline run with n-gram perceive found 70 candidates but the top results were all Read→Edit (frequency ≠ importance). Replaced with intent-first perceive using TF-IDF on prompt tokens.

### Result

Intent-first surfaces real workflows:
- **"improve"** → Read(.md) → Edit(.md) → Edit(.md)
- **"commit + push"** → Bash(git) × 5
- **"backend + sst + production"** → Bash(cd) → Bash(turso) → Bash(pnpm) → Bash(export) → Bash(curl)

Remaining weakness: single-word continuations ("yes", "fix") lose the intent from the previous turn. See [002](results/002-session-logging-harness.md).

## The fixed point operator

Qualifiers like "a bit" dampen a skill to idempotency. "Tighten every paragraph a bit" converges in two passes — the second finds almost nothing to cut. Without the qualifier, repeated application collapses the output to a single word.

This is the convergence mechanism for skill mutation. Without a dampener, each mutation drifts further. With one, mutations that overshoot get corrected on the next evaluation. The qualifier is the Filter on the Filter.

## Success criteria

The harness produces a skill that:
1. Finds more true patterns than the current skill (recall)
2. Flags fewer false patterns (precision)
3. Requires less human direction to apply fixes (autonomy)
4. Changes how the agent processes the next post (the consolidation test)

## Quick start

1. Clone this repo anywhere
2. Open the repo in Claude Code
3. Say: **"Set up the consolidation harness"**

That's it. Claude reads `CLAUDE.md`, runs `install.sh`, backfills your transcripts, and the hooks take it from there. Every session after that is indexed automatically. When enough turns accumulate, Claude will prompt you to run consolidation.

### Manual install

```bash
bash hooks/install.sh
cd harness && uv run python backfill.py
```

### Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with hooks support
- Python 3.9+
- [uv](https://docs.astral.sh/uv/)

## Prior art

- [The Flicker](https://www.june.kim/the-flicker) — the blog post documenting this experiment
- [The Natural Framework](https://www.june.kim/the-natural-framework) — the six steps
- [Diagnosis LLM](https://www.june.kim/diagnosis-llm) — SOAP notes on the agent's broken cells
- [Consolidation](https://www.june.kim/consolidation) — the procedural memory test
- [The Parts Bin](https://www.june.kim/the-parts-bin) — candidate algorithms for each cell
- [Slop Detection](https://www.june.kim/slop-detection) — two iterations to convergence

## License

AGPL-3.0-or-later

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
~/.claude/hooks/session-end-extract.py   # SessionEnd hook (thin shim)
                    │
                    ▼
Documents/agi/harness/
├── extract.py          # parse JSONL transcript → action records
├── perceive.py         # find repeating subsequences
├── cluster.py          # group similar patterns (Jaccard + edit distance)
├── filter.py           # threshold check, dedupe vs existing skills
├── propose.py          # format candidate as draft SKILL.md
├── backfill.py         # one-shot: extract all existing transcripts
├── config.py           # path constants, thresholds
├── test_extract.py     # tests
└── test_perceive.py    # tests

~/.claude/memory/
├── actions/            # one JSONL per session (action records)
├── config.json         # turn_threshold, min_coactivation
├── turn_counter.json   # accumulator, triggers consolidation
└── consolidation-due   # zero-byte marker (presence = signal)

~/.claude/skills/       # the skill store (Remember)
Documents/agi/variants/ # mutated skill candidates
Documents/agi/results/  # scoring logs
```

## The loop

```
SessionEnd hook
    │
    ▼
extract.py → ~/.claude/memory/actions/{session_id}.jsonl
    │
    └─► turn_counter.json (accumulator)
            │
            ├─ counter < N → done
            └─ counter >= N → touch consolidation-due
                                │
                                ▼
1. PERCEIVE     perceive.py — find repeating tool subsequences
2. CACHE        cluster.py  — group by Jaccard + edit distance
3. FILTER       filter.py   — reject homogeneous, below-threshold
4. ATTEND       human reviews candidates.md
5. CONSOLIDATE  propose.py → write winning pattern as SKILL.md
6. REMEMBER     skill persists in ~/.claude/skills/
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

### Test corpus

Posts from `june.kim/_posts/` with humanize results in the git history. The diff is ground truth: what the human accepted.

## The fixed point operator

Qualifiers like "a bit" dampen a skill to idempotency. "Tighten every paragraph a bit" converges in two passes — the second finds almost nothing to cut. Without the qualifier, repeated application collapses the output to a single word.

This is the convergence mechanism for skill mutation. Without a dampener, each mutation drifts further. With one, mutations that overshoot get corrected on the next evaluation. The qualifier is the Filter on the Filter.

## Success criteria

The harness produces a skill that:
1. Finds more true patterns than the current skill (recall)
2. Flags fewer false patterns (precision)
3. Requires less human direction to apply fixes (autonomy)
4. Changes how the agent processes the next post (the consolidation test)

## Prior art

- [The Flicker](https://www.june.kim/the-flicker) — the blog post documenting this experiment
- [The Natural Framework](https://www.june.kim/the-natural-framework) — the six steps
- [Diagnosis LLM](https://www.june.kim/diagnosis-llm) — SOAP notes on the agent's broken cells
- [Consolidation](https://www.june.kim/consolidation) — the procedural memory test
- [The Parts Bin](https://www.june.kim/the-parts-bin) — candidate algorithms for each cell
- [Slop Detection](https://www.june.kim/slop-detection) — two iterations to convergence

## License

AGPL-3.0-or-later

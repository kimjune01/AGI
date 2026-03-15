# AGI

Skill consolidation harness. The experiment that closes the loop.

## Thesis

Claude Code has a `create-skill` capability — the only procedure that writes procedures. That's the Consolidate cell. It's dimmed because the agent never initiates. This harness makes it automatic.

The algorithm: track which action sequences repeat with user approval across sessions. When a pattern recurs above a threshold, condense it into a skill. Score the skill against a mutation. Winner survives. Two iterations to convergence.

Three agents, three roles:
- **Codex (GPT-5.4)** — scores skill variants against the contract. The A/B test harness.
- **Claude Code** — creates and mutates skills. The skill mutator.
- **Human** — approves or rejects consolidated skills. The Attend.

## Architecture

```
~/.claude/skills/          # the skill store (Remember)
~/.claude/memory/          # session logs, co-activation counts
Documents/AGI/variants/    # mutated skill candidates
Documents/AGI/results/     # scoring logs
```

## The loop

```
1. PERCEIVE   Scan session logs for repeating action sequences
2. CACHE      Cluster by embedding similarity
3. FILTER     Reject patterns below co-activation threshold
4. ATTEND     Human reviews candidates (sleep replay)
5. CONSOLIDATE  Write winning pattern as a skill file
6. REMEMBER   Skill persists in ~/.claude/skills/
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

Posts from `june.kim/_posts/` with known humanize results in the git history. The git diff is the ground truth: what the human actually accepted.

## Success criteria

The harness produces a skill that:
1. Finds more true patterns than the current skill (recall)
2. Flags fewer false patterns (precision)
3. Requires less human direction to apply fixes (autonomy)
4. Changes how the agent processes the next post (the consolidation test)

## Prior art

- [The Natural Framework](https://www.june.kim/the-natural-framework) — the six steps
- [Diagnosis LLM](https://www.june.kim/diagnosis-llm) — SOAP notes on the agent's broken cells
- [Consolidation](https://www.june.kim/consolidation) — the procedural memory test
- [The Parts Bin](https://www.june.kim/the-parts-bin) — candidate algorithms for each cell
- [Slop Detection](https://www.june.kim/slop-detection) — two iterations to convergence

## License

AGPL-3.0-or-later

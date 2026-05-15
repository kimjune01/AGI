# AGI

**Status: concluded, null result (May 2026).** Hooks unwired; archive removed; this repo is preserved as the artifact, not as a live system.

## What it was

A consolidation harness for Claude Code. The premise: action sequences that recur across sessions with human approval are evidence of a procedure worth condensing into a skill. Wire a SessionEnd hook to extract action records, count turns, trigger a pipeline at threshold, surface candidate patterns for human approval.

Architecture in three movements:
1. **Perceive.** Extract action records from transcripts. Cluster by intent (TF-IDF on prompt tokens) rather than n-gram frequency.
2. **Filter.** Reject homogeneous patterns, below-threshold counts, candidates that can't fit a skill contract.
3. **Attend.** Human reviews `candidates.md`, picks what to consolidate.

Ran end-to-end. Extracted 27,844 actions across hundreds of sessions. Found 44 patterns, filtered to 7 candidates.

## Why it didn't pan out

The candidates were too generic to encode. Top finds:

- `Read(.md) → Edit(.md) → Edit(.md)` — the blog-edit triple
- `Edit(.css) → Bash(cd)` — CSS tweak + dir hop
- A long `Read → Edit → Bash(go) → Bash(make)` chain — Go iterate loop

None of these are skills. They're file-extension shapes. The actual knowledge that would make them useful — *which* markdown file, *what* prose pattern, *what* CSS property, *which* Go invariant — lives in the project, not in the cross-session action stream.

The framing error: skills aren't generic procedures over file types. The valuable skills already written (`humanize`, `tighten`, `sharpen`, `not-but`) are specific rewrites tied to specific patterns in a specific corpus. Cross-project pattern mining strips exactly the context that makes a skill load-bearing.

In hindsight, the right unit isn't "action sequence that repeats." It's "judgment that turned out to be correct in retrospect, in this domain." That judgment is hard to extract from logs — it lives in the moments where the user said *yeah that's right* or *no go back*. The harness recorded actions, not verdicts.

## What's worth keeping

Two findings survive the null result and have already been absorbed into other work:

**Frequency ≠ importance.** N-gram counts surface the most common file-extension shapes, which are noise. TF-IDF on prompt tokens (intent-first perceive) surfaces what the user was *trying to do*, which is closer to signal. Useful pattern for any downstream observability that wants to summarize sessions.

**"A bit" is a fixed-point operator.** Qualifiers like "a bit" dampen rewrite skills to idempotency: the second pass finds almost nothing to change. Without the qualifier, repeated application collapses the output to a stub. This is the convergence mechanism that lets composable rewrite skills (tighten, humanize, sharpen) run in a loop without drift. It's now load-bearing in those skills' contracts.

## What was wired up

For the historical record:

- `hooks/session-end-extract.py` — transcript → action records
- `hooks/consolidation-check.sh` — SessionStart prompt when turn-counter tripped
- `harness/extract.py` + `perceive.py` + `cluster.py` + `filter.py` + `propose.py` + `run_pipeline.py`
- State directories at `~/.claude/memory/{actions/,turn_counter.json,config.json,consolidation-due}`

All of the above has been removed from the live environment. The code remains in this repo.

## How to revive (if you want to)

```bash
bash hooks/install.sh
cd harness && uv run python backfill.py
```

But don't, unless the framing has shifted. The substrate works; the premise is what failed.

## Prior art

- [The Flicker](https://www.june.kim/the-flicker) — the blog post that motivated this experiment
- [The Natural Framework](https://www.june.kim/the-natural-framework) — Consolidate as the backward pass
- [Slop Detection](https://www.june.kim/slop-detection) — where the two-passes-to-convergence pattern came from

## License

AGPL-3.0-or-later

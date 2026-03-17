# Experiment 2: Session Logging Harness

## Goal
Close the structural gap: nothing was writing to the store between sessions, and nothing was triggering the pipeline. Build the Perceive cell.

## What was built
- `SessionEnd` hook extracts action records from every transcript
- Backfill indexed 446 existing transcripts → 13,427 action records
- Full pipeline: perceive → cluster → filter → propose

## Results (first run)
- 12,509 approved actions loaded
- 799 patterns at min_count=10
- 294 clusters after Jaccard + edit distance grouping
- 70 candidates after filtering homogeneous and below-threshold

Top 5 candidates:

| Pattern | Count | Sessions |
|---------|-------|----------|
| Read(.md) → Edit(.md) | 3,401 | 149 |
| Read(.tsx) → Edit(.tsx) | 2,385 | 40 |
| Read(.go) → Edit(.go) | 1,665 | 54 |
| TaskCreate → TaskUpdate | 1,207 | 87 |
| Read(.ts) → Edit(.ts) | 905 | 46 |

## Assessment
**The plumbing works. The signal is weak.**

Two problems:

1. **N-grams are the wrong lens.** The patterns worth consolidating aren't frequency-ranked n-grams — they're intent clusters. "Edit a blog post" is Read→Skill(humanize)→Edit→Edit→Skill(tighten)→Bash(deploy). That 6-step sequence appears maybe 20 times but will never outrank Read→Edit at 3,400x. Frequency ≠ importance.

2. **The discriminator strips too much.** `("Read", ".md")` loses which file and why. Two sessions both doing Read(.md)→Edit(.md) could be unrelated tasks. The 80-char prompt prefix helps but is noisy.

## Next step
Flip the pipeline: cluster by prompt similarity first (what was the user trying to do?), then find tool sequences within each intent cluster. That's the actual Perceive→Cache ordering — perceive the intent, cache the actions. The current v1 perceives actions and tries to infer intent from frequency. Backwards.

## Decision
**Keep the plumbing, replace the perceive step.** The hook, store, and turn trigger are sound infrastructure. `perceive.py` needs to work on intent tokens (from prompt prefixes) not tool n-grams.

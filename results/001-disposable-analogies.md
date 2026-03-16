# Experiment 1, Round 1: Disposable Analogies

## Mutation
Add "Disposable analogies" pattern: flag analogies that explain the point less clearly than the literal version ("the same mechanism that keeps a thermostat from..." → state the mechanism directly).

## Source
Codex proposed from ground truth diff of `set-it-forget-it` (commit e4e4749). Human cut a thermostat analogy in favor of "Overshoot, correct, settle."

## Scoring
Tested both variants on `copyleft-pagerank` (commit 46418b4).

| Variant | Recall | Precision | False Positives |
|---|---|---|---|
| A (current) | 5/7 | 5/9 | 4 |
| B (+disposable analogies) | 5/7 | 5/9 | 4 |

The new pattern didn't fire on the test post. No recall gain, no precision loss.

## Decision
**A wins on parsimony.** The mutation is real but too narrow for one occurrence. Hold for re-evaluation if it fires on a second post.

## Observations
- Em dash detection drove most of the recall (4/5 true positives)
- The skill misses: precision edits ("partition theory" → "theory"), phrasing sharpening ("could?" → "could be found?")
- Those misses are line-editing, not pattern-matching. They're Attend-level, not Filter-level.
- 4 false positives suggest rule-of-three and stock-metaphor thresholds may need tightening

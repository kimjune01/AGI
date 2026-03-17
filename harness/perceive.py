"""Perceive: scan action store for repeating tool subsequences.

Finds n-gram tool sequences that recur across sessions above a threshold.
These are candidates for skill consolidation.
"""

import json
from collections import Counter
from pathlib import Path


def load_actions(
    actions_dir: Path,
    approved_only: bool = False,
    project: str | None = None,
) -> list[dict]:
    """Load action records from JSONL files in actions_dir."""
    actions = []
    for f in sorted(actions_dir.glob("*.jsonl")):
        for line in f.read_text().strip().split("\n"):
            if not line:
                continue
            try:
                a = json.loads(line)
            except json.JSONDecodeError:
                continue
            if approved_only and not a.get("approved", False):
                continue
            if project and a.get("project") != project:
                continue
            actions.append(a)
    return actions


def _extract_ngrams(
    tool_sequence: list[list[str]],
    min_length: int,
    max_length: int,
) -> list[tuple[tuple[str, str], ...]]:
    """Extract all n-grams of length min_length..max_length from a tool sequence."""
    seq = [tuple(t) for t in tool_sequence]
    ngrams = []
    for n in range(min_length, min(max_length, len(seq)) + 1):
        for i in range(len(seq) - n + 1):
            ngrams.append(tuple(seq[i:i + n]))
    return ngrams


def find_patterns(
    actions: list[dict],
    min_count: int = 3,
    min_length: int = 2,
    max_length: int = 6,
) -> list[dict]:
    """Find repeating tool subsequences across actions.

    Returns list of pattern dicts sorted by count descending:
    {
        "sequence": [(tool, discriminator), ...],
        "count": int,
        "sessions": set of session_ids,
        "example_prompts": [str, ...]
    }
    """
    # Count n-grams
    ngram_counter: Counter[tuple] = Counter()
    ngram_sessions: dict[tuple, set[str]] = {}
    ngram_prompts: dict[tuple, list[str]] = {}

    for action in actions:
        seq = action.get("tool_sequence", [])
        if not seq:
            continue
        session_id = action.get("session_id", "")
        prompt = action.get("prompt_prefix", "")

        for ngram in _extract_ngrams(seq, min_length, max_length):
            ngram_counter[ngram] += 1
            if ngram not in ngram_sessions:
                ngram_sessions[ngram] = set()
                ngram_prompts[ngram] = []
            ngram_sessions[ngram].add(session_id)
            if len(ngram_prompts[ngram]) < 5:
                ngram_prompts[ngram].append(prompt)

    # Filter by min_count
    patterns = []
    for ngram, count in ngram_counter.most_common():
        if count < min_count:
            break
        patterns.append({
            "sequence": list(ngram),
            "count": count,
            "sessions": len(ngram_sessions[ngram]),
            "example_prompts": ngram_prompts[ngram],
        })

    return patterns

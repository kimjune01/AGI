"""Perceive: find repeating patterns in the action store.

Two modes:
1. intent-first (default): cluster actions by prompt similarity, then find
   the canonical tool sequence for each intent cluster.
2. ngram (legacy): frequency-ranked tool n-grams across all actions.

Intent-first is the correct pipeline ordering (perceive the intent, cache the
actions). N-gram mode is kept for comparison.
"""

import json
import math
import re
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


# --- Intent-first mode ---

# Noise words and system artifacts to strip from prompts
_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "about", "up", "down",
    "and", "but", "or", "if", "while", "that", "this", "it", "its",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "they",
    "them", "what", "which", "who", "whom", "these", "those",
    # System noise
    "request", "interrupted", "user", "local", "command", "caveat",
    "messages", "below", "session", "being", "resumed", "base",
    "directory", "continued", "previous", "conversation", "tool",
    "use", "ran", "source", "image", "original", "displayed",
    "multiply", "coordinates", "skill", "users",
}

# Patterns to strip from prompts before tokenizing
_NOISE_PATTERNS = [
    r"<[^>]+>",           # XML/HTML tags
    r"\[image:[^\]]+\]",  # Image references
    r"\[request[^\]]*\]", # Interruption markers
    r"https?://\S+",      # URLs
    r"/[Uu]sers/\S+",     # Absolute paths
    r"[^a-zA-Z0-9/\- ]",  # Non-alphanumeric (keep slashes for /commands)
]

# Prompts that are pure system noise — skip entirely
_SKIP_PREFIXES = [
    "[request interrupted",
    "this session is being continued",
    "base directory for this",
    "[image:",
]


def _tokenize_prompt(prompt: str) -> list[str]:
    """Extract intent-bearing tokens from a prompt prefix."""
    text = prompt.lower()
    for pat in _NOISE_PATTERNS:
        text = re.sub(pat, " ", text)
    words = text.split()
    tokens = [w for w in words if w not in _STOP_WORDS and len(w) > 1]
    return tokens


def _compute_idf(actions: list[dict]) -> dict[str, float]:
    """Compute inverse document frequency for prompt tokens."""
    n = len(actions)
    if n == 0:
        return {}
    doc_freq: Counter[str] = Counter()
    for a in actions:
        tokens = set(_tokenize_prompt(a.get("prompt_prefix", "")))
        for t in tokens:
            doc_freq[t] += 1
    return {t: math.log(n / df) for t, df in doc_freq.items()}


def _intent_signature(prompt: str, idf: dict[str, float], top_k: int = 3) -> tuple[str, ...]:
    """Extract the top-k highest-IDF tokens as an intent signature."""
    tokens = _tokenize_prompt(prompt)
    if not tokens:
        return ()
    scored = [(t, idf.get(t, 0)) for t in tokens]
    scored.sort(key=lambda x: -x[1])
    # Dedupe while preserving order
    seen = set()
    result = []
    for t, _ in scored:
        if t not in seen:
            seen.add(t)
            result.append(t)
            if len(result) >= top_k:
                break
    return tuple(result)


def find_intent_patterns(
    actions: list[dict],
    min_count: int = 5,
    top_k_tokens: int = 3,
) -> list[dict]:
    """Find patterns by clustering on intent, then extracting tool sequences.

    Groups actions by their top-k IDF-weighted prompt tokens, then finds
    the most common tool sequence within each group.

    Returns list of intent pattern dicts sorted by count:
    {
        "intent": ("token1", "token2", ...),
        "count": int,
        "sessions": int,
        "canonical_sequence": [(tool, discriminator), ...],
        "sequence_variants": {sequence_tuple: count},
        "example_prompts": [str, ...],
    }
    """
    if not actions:
        return []

    idf = _compute_idf(actions)

    # Group by intent signature
    groups: dict[tuple, list[dict]] = {}
    for a in actions:
        prompt = a.get("prompt_prefix", "")
        # Skip system noise prompts
        if any(prompt.lower().startswith(p) for p in _SKIP_PREFIXES):
            continue
        sig = _intent_signature(prompt, idf, top_k_tokens)
        if not sig:
            continue
        groups.setdefault(sig, []).append(a)

    # For each group, find the canonical tool sequence
    patterns = []
    for intent, members in groups.items():
        if len(members) < min_count:
            continue

        # Count tool sequences
        seq_counter: Counter[tuple] = Counter()
        sessions: set[str] = set()
        prompts: list[str] = []

        for a in members:
            seq = tuple(tuple(t) for t in a.get("tool_sequence", []))
            if seq:  # Skip empty sequences
                seq_counter[seq] += 1
            sessions.add(a.get("session_id", ""))
            if len(prompts) < 5:
                prompts.append(a.get("prompt_prefix", ""))

        if not seq_counter:
            continue

        canonical = seq_counter.most_common(1)[0][0]

        patterns.append({
            "intent": intent,
            "count": len(members),
            "sessions": len(sessions),
            "canonical_sequence": list(canonical),
            "sequence_variants": {str(k): v for k, v in seq_counter.most_common(5)},
            "example_prompts": prompts,
        })

    patterns.sort(key=lambda p: -p["count"])
    return patterns


# --- N-gram mode (legacy) ---

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
    """Find repeating tool subsequences across actions (legacy n-gram mode).

    Returns list of pattern dicts sorted by count descending:
    {
        "sequence": [(tool, discriminator), ...],
        "count": int,
        "sessions": int,
        "example_prompts": [str, ...]
    }
    """
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

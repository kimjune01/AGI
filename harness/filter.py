"""Filter: threshold check and dedupe against existing skills.

Rejects patterns that are:
- Below the co-activation threshold (too rare to be a real workflow)
- Homogeneous (all same tool — just repetition, not a workflow)
- Already captured by an existing skill
"""

import json
from pathlib import Path

from config import MEMORY_CONFIG, DEFAULT_MIN_COACTIVATION


def _is_homogeneous(sequence: list[tuple]) -> bool:
    """True if all tools in the sequence are the same."""
    if len(sequence) <= 1:
        return True
    tool_names = {t[0] for t in sequence}
    return len(tool_names) == 1


def _load_existing_skills() -> list[str]:
    """Load names of existing skills from ~/.claude/skills/."""
    skills_dir = Path.home() / ".claude" / "skills"
    if not skills_dir.exists():
        return []
    return [d.name for d in skills_dir.iterdir() if d.is_dir()]


def _load_config() -> dict:
    """Load config from memory config file."""
    if MEMORY_CONFIG.exists():
        try:
            return json.loads(MEMORY_CONFIG.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def filter_clusters(
    clusters: list[dict],
    min_sessions: int | None = None,
    min_count: int | None = None,
) -> list[dict]:
    """Filter clusters, returning only actionable candidates.

    Args:
        clusters: from cluster_patterns()
        min_sessions: minimum distinct sessions (default: from config min_coactivation)
        min_count: minimum total count (default: 10)

    Returns filtered list of clusters.
    """
    cfg = _load_config()
    if min_sessions is None:
        min_sessions = cfg.get("min_coactivation", DEFAULT_MIN_COACTIVATION)
    if min_count is None:
        min_count = 10

    existing_skills = set(_load_existing_skills())

    candidates = []
    for cluster in clusters:
        rep = cluster["representative"]
        seq = rep["sequence"]

        # Skip homogeneous patterns (Edit→Edit→Edit)
        if _is_homogeneous(seq):
            continue

        # Skip below session threshold
        if cluster["total_sessions"] < min_sessions:
            continue

        # Skip below count threshold
        if cluster["total_count"] < min_count:
            continue

        # Skip if matches an existing skill name pattern
        # (heuristic: check if prompt prefixes suggest an existing skill)
        prompts = rep.get("example_prompts", [])
        skill_match = False
        for skill in existing_skills:
            for prompt in prompts:
                if skill.lower() in prompt.lower():
                    skill_match = True
                    break
            if skill_match:
                break

        if skill_match:
            continue

        candidates.append(cluster)

    return candidates

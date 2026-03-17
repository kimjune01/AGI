"""Run the full consolidation pipeline: perceive → cluster → filter → propose."""

from pathlib import Path

from cluster import cluster_patterns
from config import ACTIONS_DIR
from filter import filter_clusters
from perceive import find_intent_patterns, load_actions
from propose import propose_all


def main():
    actions = load_actions(ACTIONS_DIR, approved_only=True)
    print(f"Loaded {len(actions)} approved actions")

    patterns = find_intent_patterns(actions, min_count=10, top_k_tokens=3)
    print(f"Found {len(patterns)} intent patterns")

    # Intent patterns don't need clustering (already clustered by intent)
    # But we filter them
    # Convert to cluster format for filter compatibility
    clusters = []
    for p in patterns:
        clusters.append({
            "representative": {
                "sequence": [tuple(t) for t in p["canonical_sequence"]],
                "count": p["count"],
                "sessions": p["sessions"],
                "example_prompts": p["example_prompts"],
            },
            "members": [{
                "sequence": [tuple(t) for t in p["canonical_sequence"]],
                "count": p["count"],
                "sessions": p["sessions"],
                "example_prompts": p["example_prompts"],
            }],
            "total_count": p["count"],
            "total_sessions": p["sessions"],
            "intent": p["intent"],
        })

    candidates = filter_clusters(clusters, min_sessions=3, min_count=10)
    print(f"Filtered to {len(candidates)} candidates")

    if candidates:
        outdir = Path(__file__).parent / "candidates"
        propose_all(candidates, outdir)
        print(f"\nWrote candidates to {outdir}/candidates.md")

    print("\nTop patterns:")
    for p in patterns[:15]:
        intent = " + ".join(p["intent"])
        seq = " → ".join(f"{t[0]}({t[1]})" for t in p["canonical_sequence"])
        print(f"  {p['count']:4d}x [{intent}] → {seq}")


if __name__ == "__main__":
    main()

"""Cluster: group similar tool-sequence patterns using Jaccard + edit distance.

Uses union-find to merge patterns that are similar enough, producing
representative clusters ranked by total count.
"""


def _jaccard(a: set, b: set) -> float:
    """Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union > 0 else 0.0


def _edit_distance(a: list, b: list) -> int:
    """Levenshtein edit distance between two sequences."""
    n, m = len(a), len(b)
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, m + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[m]


def _normalized_edit_similarity(a: list, b: list) -> float:
    """1 - (edit_distance / max_length). Returns 0..1."""
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 1.0
    return 1.0 - _edit_distance(a, b) / max_len


def _similarity(pattern_a: dict, pattern_b: dict) -> float:
    """Combined similarity: average of Jaccard (tool set) and normalized edit distance."""
    seq_a = pattern_a["sequence"]
    seq_b = pattern_b["sequence"]

    set_a = set(seq_a)
    set_b = set(seq_b)

    jaccard = _jaccard(set_a, set_b)
    edit_sim = _normalized_edit_similarity(list(seq_a), list(seq_b))

    return (jaccard + edit_sim) / 2


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1


def cluster_patterns(
    patterns: list[dict],
    similarity_threshold: float = 0.7,
) -> list[dict]:
    """Group similar patterns using union-find.

    Returns list of cluster dicts, each with:
    - representative: the highest-count pattern in the cluster
    - members: list of all patterns in the cluster
    - total_count: sum of counts across all members
    - total_sessions: max sessions across members (conservative estimate)
    """
    n = len(patterns)
    if n == 0:
        return []

    uf = UnionFind(n)

    # Compare all pairs (O(n^2) but n is small after min_count filtering)
    for i in range(n):
        for j in range(i + 1, n):
            if _similarity(patterns[i], patterns[j]) >= similarity_threshold:
                uf.union(i, j)

    # Group by root
    groups: dict[int, list[int]] = {}
    for i in range(n):
        root = uf.find(i)
        groups.setdefault(root, []).append(i)

    # Build cluster dicts
    clusters = []
    for indices in groups.values():
        members = [patterns[i] for i in indices]
        # Representative = highest count member
        representative = max(members, key=lambda m: m["count"])
        total_count = sum(m["count"] for m in members)
        total_sessions = max(m["sessions"] for m in members)

        clusters.append({
            "representative": representative,
            "members": members,
            "total_count": total_count,
            "total_sessions": total_sessions,
        })

    clusters.sort(key=lambda c: c["total_count"], reverse=True)
    return clusters

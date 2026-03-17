"""Propose: format approved candidates as draft SKILL.md files.

Takes filtered clusters and generates a markdown skill description
that could be installed into ~/.claude/skills/.
"""

from datetime import datetime, timezone
from pathlib import Path


def _format_sequence(seq: list[tuple]) -> str:
    """Format a tool sequence as a readable string."""
    return " → ".join(f"{t[0]}({t[1]})" if t[1] else t[0] for t in seq)


def propose_skill(cluster: dict, output_dir: Path | None = None) -> str:
    """Generate a draft SKILL.md from a pattern cluster.

    Returns the markdown content. If output_dir is given, also writes to file.
    """
    rep = cluster["representative"]
    seq = rep["sequence"]
    prompts = rep.get("example_prompts", [])

    # Derive a name from the sequence
    tool_names = [t[0] for t in seq]
    name = "-".join(dict.fromkeys(tool_names)).lower()  # dedupe, preserve order

    lines = [
        f"# Draft Skill: {name}",
        "",
        f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"**Pattern count**: {cluster['total_count']} across {cluster['total_sessions']} sessions",
        "",
        "## Trigger pattern",
        "",
        f"`{_format_sequence(seq)}`",
        "",
    ]

    # Show cluster variants
    if len(cluster["members"]) > 1:
        lines.append("### Variants")
        lines.append("")
        for m in sorted(cluster["members"], key=lambda x: -x["count"])[:5]:
            lines.append(f"- `{_format_sequence(m['sequence'])}` ({m['count']}x)")
        lines.append("")

    # Show example prompts
    if prompts:
        lines.append("## Example prompts")
        lines.append("")
        for p in prompts[:5]:
            lines.append(f"- {p}")
        lines.append("")

    # Skill template
    lines.extend([
        "## Proposed skill logic",
        "",
        "```",
        "# TODO: Define the skill contract",
        f"# Input: (derived from prompts above)",
        f"# Output: (derived from tool sequence)",
        f"# Steps: {' → '.join(tool_names)}",
        "```",
        "",
        "## Status",
        "",
        "- [ ] Reviewed by human",
        "- [ ] Tested on corpus",
        "- [ ] Installed as skill",
        "",
    ])

    content = "\n".join(lines)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        outfile = output_dir / f"{name}.md"
        outfile.write_text(content)

    return content


def propose_all(clusters: list[dict], output_dir: Path) -> list[Path]:
    """Generate draft skills for all candidate clusters.

    Returns list of written file paths.
    """
    files = []
    for cluster in clusters:
        rep = cluster["representative"]
        seq = rep["sequence"]
        tool_names = [t[0] for t in seq]
        name = "-".join(dict.fromkeys(tool_names)).lower()

        propose_skill(cluster, output_dir)
        files.append(output_dir / f"{name}.md")

    # Also write a candidates.md summary
    summary_lines = [
        "# Skill Candidates",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "| # | Pattern | Count | Sessions | File |",
        "|---|---------|-------|----------|------|",
    ]
    for i, cluster in enumerate(clusters, 1):
        rep = cluster["representative"]
        seq_str = _format_sequence(rep["sequence"])
        tool_names = [t[0] for t in rep["sequence"]]
        name = "-".join(dict.fromkeys(tool_names)).lower()
        summary_lines.append(
            f"| {i} | `{seq_str}` | {cluster['total_count']} | {cluster['total_sessions']} | [{name}.md]({name}.md) |"
        )

    summary = "\n".join(summary_lines) + "\n"
    summary_path = output_dir / "candidates.md"
    summary_path.write_text(summary)
    files.append(summary_path)

    return files

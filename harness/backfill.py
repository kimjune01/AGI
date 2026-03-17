#!/usr/bin/env python3
"""One-shot backfill: run extract on all existing transcripts.

Scans ~/.claude/projects/ for JSONL transcripts and extracts action records
into ~/.claude/memory/actions/.
"""

import sys
from pathlib import Path

from config import ACTIONS_DIR, PROJECTS_DIR
from extract import extract_actions


def derive_project(project_dir_name: str) -> str:
    """Derive project name from directory name.

    e.g. "-Users-junekim-Documents-june-kim" → "june-kim"
    """
    parts = project_dir_name.strip("-").split("-")
    # Find the part after "Documents-" (or last segment)
    try:
        doc_idx = parts.index("Documents")
        return "-".join(parts[doc_idx + 1:]) if doc_idx + 1 < len(parts) else parts[-1]
    except ValueError:
        return parts[-1] if parts else "unknown"


def backfill():
    if not PROJECTS_DIR.exists():
        print(f"Projects dir not found: {PROJECTS_DIR}")
        return

    total_files = 0
    total_actions = 0

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue
        # Skip temp/test dirs
        if "private-var" in project_dir.name or "pytest" in project_dir.name:
            continue

        project = derive_project(project_dir.name)
        transcripts = list(project_dir.glob("*.jsonl"))
        if not transcripts:
            continue

        for transcript in transcripts:
            session_id = transcript.stem
            # Skip if already extracted
            outfile = ACTIONS_DIR / f"{session_id}.jsonl"
            if outfile.exists():
                continue

            try:
                n = extract_actions(transcript, ACTIONS_DIR, session_id, project)
                total_files += 1
                total_actions += n
                print(f"  {project}/{session_id}: {n} actions")
            except Exception as e:
                print(f"  ERROR {project}/{session_id}: {e}", file=sys.stderr)

    print(f"\nBackfill complete: {total_files} transcripts → {total_actions} actions")
    print(f"Output: {ACTIONS_DIR}")


if __name__ == "__main__":
    backfill()

#!/usr/bin/env python3
"""SessionEnd hook: extract action records from the transcript.

Reads hook input from stdin, runs extract.py on the transcript,
updates the turn counter, and touches consolidation-due marker if threshold met.

Finds the harness directory relative to this script's installed location
via ~/.claude/memory/harness_path, written by install.sh.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

MEMORY_DIR = Path.home() / ".claude" / "memory"
ACTIONS_DIR = MEMORY_DIR / "actions"
TURN_COUNTER = MEMORY_DIR / "turn_counter.json"
CONSOLIDATION_DUE = MEMORY_DIR / "consolidation-due"
MEMORY_CONFIG = MEMORY_DIR / "config.json"
HARNESS_PATH_FILE = MEMORY_DIR / "harness_path"


def _find_harness() -> Optional[Path]:
    """Resolve harness directory from the stored path."""
    if HARNESS_PATH_FILE.exists():
        p = Path(HARNESS_PATH_FILE.read_text().strip())
        if p.exists():
            return p
    return None


def main():
    hook_input = json.loads(sys.stdin.read())
    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", "")

    if not transcript_path or not Path(transcript_path).exists():
        return

    harness = _find_harness()
    if not harness:
        return

    sys.path.insert(0, str(harness))

    project = cwd.rstrip("/").rsplit("/", 1)[-1].replace(".", "-") if cwd else "unknown"

    from extract import extract_actions
    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    n = extract_actions(Path(transcript_path), ACTIONS_DIR, session_id, project)

    counter = {"count": 0, "last_reset": datetime.now(timezone.utc).isoformat()}
    if TURN_COUNTER.exists():
        try:
            counter = json.loads(TURN_COUNTER.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    counter["count"] = counter.get("count", 0) + n
    TURN_COUNTER.write_text(json.dumps(counter) + "\n")

    threshold = 1000
    if MEMORY_CONFIG.exists():
        try:
            cfg = json.loads(MEMORY_CONFIG.read_text())
            threshold = cfg.get("turn_threshold", 1000)
        except (json.JSONDecodeError, OSError):
            pass

    if counter["count"] >= threshold:
        CONSOLIDATION_DUE.touch()


if __name__ == "__main__":
    main()

"""Path constants and thresholds for the consolidation harness."""

from pathlib import Path

# Directories
CLAUDE_DIR = Path.home() / ".claude"
MEMORY_DIR = CLAUDE_DIR / "memory"
ACTIONS_DIR = MEMORY_DIR / "actions"
PROJECTS_DIR = CLAUDE_DIR / "projects"

# Config files
MEMORY_CONFIG = MEMORY_DIR / "config.json"
TURN_COUNTER = MEMORY_DIR / "turn_counter.json"
CONSOLIDATION_DUE = MEMORY_DIR / "consolidation-due"

# Thresholds
DEFAULT_TURN_THRESHOLD = 100
DEFAULT_MIN_COACTIVATION = 3

"""Parse Claude Code transcript JSONL into action records.

Each transcript is a sequence of messages (user, assistant, tool_result, etc).
We extract one action record per user→assistant turn, capturing the tool
sequence used and whether the turn was approved (not interrupted).
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def normalize_tool(tool_name: str, tool_input: dict) -> tuple[str, str]:
    """Normalize a tool invocation to (tool_name, discriminator).

    File tools → file extension. Bash → first command word. Skill → skill name.
    """
    # File-based tools: extract extension from file_path
    if tool_name in ("Read", "Edit", "Write", "NotebookEdit"):
        fp = tool_input.get("file_path", tool_input.get("notebook_path", ""))
        _, ext = os.path.splitext(fp)
        return (tool_name, ext)

    if tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        # Extract the extension-like suffix from glob patterns
        # e.g. "**/*.ts" → ".ts", "src/**/*.{ts,tsx}" → ".{ts,tsx}"
        if "*." in pattern:
            ext_part = pattern.rsplit("*.", 1)[-1]
            return (tool_name, "." + ext_part)
        return (tool_name, "")

    if tool_name == "Grep":
        glob = tool_input.get("glob", "")
        if glob and "." in glob:
            ext_part = glob.rsplit(".", 1)[-1]
            return (tool_name, "." + ext_part)
        return (tool_name, "")

    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        # First word, strip path prefix
        first_word = cmd.split()[0] if cmd.split() else ""
        first_word = first_word.rsplit("/", 1)[-1]
        return (tool_name, first_word)

    if tool_name == "Skill":
        return (tool_name, tool_input.get("skill", ""))

    if tool_name == "Task":
        desc = tool_input.get("description", "")
        return (tool_name, desc)

    return (tool_name, "")


def _is_user_text_message(entry: dict) -> bool:
    """True if this entry is a user text message (not a tool result)."""
    if entry.get("type") != "user":
        return False
    msg = entry.get("message", {})
    content = msg.get("content", "")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return any(c.get("type") == "text" for c in content)
    return False


def _is_interruption(entry: dict) -> bool:
    """True if this is a user interruption message."""
    msg = entry.get("message", {})
    content = msg.get("content", "")
    if isinstance(content, str):
        return "[Request interrupted by user]" in content
    if isinstance(content, list):
        for c in content:
            if c.get("type") == "text" and "[Request interrupted by user]" in c.get("text", ""):
                return True
    return False


def _extract_prompt_prefix(content, max_chars: int = 80) -> str:
    """Extract first max_chars of user prompt text."""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = [c.get("text", "") for c in content if c.get("type") == "text"]
        text = " ".join(parts)
    else:
        text = ""
    text = text.strip().replace("\n", " ")
    return text[:max_chars]


def _extract_tools(entry: dict) -> list[list[str]]:
    """Extract normalized tool calls from an assistant message."""
    msg = entry.get("message", {})
    content = msg.get("content", [])
    if not isinstance(content, list):
        return []
    tools = []
    for block in content:
        if block.get("type") == "tool_use":
            name = block.get("name", "")
            inp = block.get("input", {})
            norm = normalize_tool(name, inp)
            tools.append(list(norm))
    return tools


def parse_transcript(path: Path) -> list[dict]:
    """Parse a transcript JSONL file into action records.

    Returns a list of action records, one per user→assistant turn.
    """
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Skip non-message types
            if entry.get("type") not in ("user", "assistant"):
                continue
            entries.append(entry)

    # Group into turns: user text message → assistant responses → next user text message
    turns = []
    current_turn = None

    for entry in entries:
        if _is_user_text_message(entry) and not _is_interruption(entry):
            # Start a new turn
            if current_turn is not None:
                current_turn["approved"] = True  # Previous turn completed normally
                turns.append(current_turn)
            current_turn = {
                "session_id": entry.get("sessionId", ""),
                "project": _derive_project(entry.get("cwd", "")),
                "timestamp": entry.get("timestamp", ""),
                "prompt_prefix": _extract_prompt_prefix(entry.get("message", {}).get("content", "")),
                "tool_sequence": [],
                "approved": False,  # Default, updated when next turn starts
            }
        elif _is_interruption(entry):
            # Interruption ends current turn as not approved
            if current_turn is not None:
                current_turn["approved"] = False
                turns.append(current_turn)
                current_turn = None
        elif entry.get("type") == "assistant" and current_turn is not None:
            tools = _extract_tools(entry)
            current_turn["tool_sequence"].extend(tools)

    # Last turn: not followed by another user message, so approved = True
    # (session ended normally, not interrupted)
    if current_turn is not None:
        # If last user message was a new prompt with no interruption, mark approved
        current_turn["approved"] = True
        turns.append(current_turn)

    # Add turn indices
    for i, turn in enumerate(turns):
        turn["turn_index"] = i

    return turns


def _derive_project(cwd: str) -> str:
    """Derive project name from cwd. e.g. /Users/junekim/Documents/june.kim → june-kim."""
    parts = cwd.rstrip("/").rsplit("/", 1)
    name = parts[-1] if parts else ""
    return name.replace(".", "-")


def extract_actions(
    transcript_path: Path,
    output_dir: Path,
    session_id: str,
    project: str,
) -> int:
    """Extract action records from a transcript and write to output_dir.

    Returns number of action records written.
    """
    actions = parse_transcript(transcript_path)

    # Override session_id and project from caller (more reliable than transcript)
    for a in actions:
        a["session_id"] = session_id
        a["project"] = project

    output_dir.mkdir(parents=True, exist_ok=True)
    outfile = output_dir / f"{session_id}.jsonl"

    with open(outfile, "w") as f:
        for a in actions:
            f.write(json.dumps(a) + "\n")

    return len(actions)

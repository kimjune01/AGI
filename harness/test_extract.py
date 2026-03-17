"""Tests for extract.py — transcript JSONL → action records."""

import json
import tempfile
from pathlib import Path

from extract import extract_actions, normalize_tool, parse_transcript


def _make_line(type_: str, **kwargs):
    """Build a minimal transcript line."""
    base = {"type": type_, "sessionId": "test-session", "timestamp": "2026-03-17T01:00:00Z"}
    base.update(kwargs)
    return json.dumps(base)


def _user_msg(content: str, uuid: str = "u1", parent: str = None):
    return json.dumps({
        "type": "user",
        "sessionId": "test-session",
        "cwd": "/Users/junekim/Documents/june.kim",
        "uuid": uuid,
        "parentUuid": parent,
        "timestamp": "2026-03-17T01:00:00Z",
        "message": {"role": "user", "content": content},
    })


def _assistant_tool(tool_name: str, tool_input: dict, uuid: str = "a1", parent: str = "u1"):
    return json.dumps({
        "type": "assistant",
        "sessionId": "test-session",
        "cwd": "/Users/junekim/Documents/june.kim",
        "uuid": uuid,
        "parentUuid": parent,
        "timestamp": "2026-03-17T01:01:00Z",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "toolu_1", "name": tool_name, "input": tool_input}
            ],
        },
    })


def _assistant_text(text: str, uuid: str = "a1", parent: str = "u1"):
    return json.dumps({
        "type": "assistant",
        "sessionId": "test-session",
        "cwd": "/Users/junekim/Documents/june.kim",
        "uuid": uuid,
        "parentUuid": parent,
        "timestamp": "2026-03-17T01:01:00Z",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
        },
    })


def _tool_result(tool_use_id: str = "toolu_1", content: str = "ok", is_error: bool = False,
                 uuid: str = "tr1", parent: str = "a1"):
    return json.dumps({
        "type": "user",
        "sessionId": "test-session",
        "uuid": uuid,
        "parentUuid": parent,
        "timestamp": "2026-03-17T01:01:01Z",
        "message": {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": tool_use_id, "content": content, "is_error": is_error}
            ],
        },
    })


# --- normalize_tool tests ---

class TestNormalizeTool:
    def test_read_file(self):
        assert normalize_tool("Read", {"file_path": "/foo/bar/post.md"}) == ("Read", ".md")

    def test_edit_file(self):
        assert normalize_tool("Edit", {"file_path": "/x/y.tsx", "old_string": "a", "new_string": "b"}) == ("Edit", ".tsx")

    def test_write_file(self):
        assert normalize_tool("Write", {"file_path": "/a/b/c.py", "content": "x"}) == ("Write", ".py")

    def test_glob(self):
        assert normalize_tool("Glob", {"pattern": "**/*.ts"}) == ("Glob", ".ts")

    def test_glob_complex_pattern(self):
        assert normalize_tool("Glob", {"pattern": "src/**/*.{ts,tsx}"}) == ("Glob", ".{ts,tsx}")

    def test_grep(self):
        assert normalize_tool("Grep", {"pattern": "foo", "glob": "*.py"}) == ("Grep", ".py")

    def test_grep_no_glob(self):
        assert normalize_tool("Grep", {"pattern": "foo"}) == ("Grep", "")

    def test_bash_simple(self):
        assert normalize_tool("Bash", {"command": "git status"}) == ("Bash", "git")

    def test_bash_with_path(self):
        assert normalize_tool("Bash", {"command": "/usr/bin/git log --oneline"}) == ("Bash", "git")

    def test_skill(self):
        assert normalize_tool("Skill", {"skill": "humanize"}) == ("Skill", "humanize")

    def test_task(self):
        assert normalize_tool("Task", {"description": "explore", "prompt": "..."}) == ("Task", "explore")

    def test_unknown_tool(self):
        assert normalize_tool("WebSearch", {"query": "test"}) == ("WebSearch", "")


# --- parse_transcript tests ---

class TestParseTranscript:
    def test_single_turn(self):
        lines = [
            _user_msg("improve the post about unions"),
            _assistant_tool("Read", {"file_path": "/posts/union.md"}, uuid="a1", parent="u1"),
            _tool_result("toolu_1", "file content", uuid="tr1", parent="a1"),
            _assistant_tool("Edit", {"file_path": "/posts/union.md", "old_string": "a", "new_string": "b"}, uuid="a2", parent="tr1"),
            _tool_result("toolu_1", "ok", uuid="tr2", parent="a2"),
        ]
        transcript = "\n".join(lines) + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(transcript)
            f.flush()
            actions = parse_transcript(Path(f.name))

        assert len(actions) == 1
        a = actions[0]
        assert a["session_id"] == "test-session"
        assert a["tool_sequence"] == [["Read", ".md"], ["Edit", ".md"]]
        assert a["prompt_prefix"].startswith("improve the post")

    def test_multiple_turns(self):
        lines = [
            _user_msg("first prompt", uuid="u1"),
            _assistant_tool("Read", {"file_path": "/a.md"}, uuid="a1", parent="u1"),
            _tool_result("toolu_1", "ok", uuid="tr1", parent="a1"),
            _user_msg("second prompt", uuid="u2", parent="a1"),
            _assistant_tool("Bash", {"command": "git status"}, uuid="a2", parent="u2"),
            _tool_result("toolu_1", "ok", uuid="tr2", parent="a2"),
        ]
        transcript = "\n".join(lines) + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(transcript)
            f.flush()
            actions = parse_transcript(Path(f.name))

        assert len(actions) == 2
        assert actions[0]["turn_index"] == 0
        assert actions[0]["tool_sequence"] == [["Read", ".md"]]
        assert actions[1]["turn_index"] == 1
        assert actions[1]["tool_sequence"] == [["Bash", "git"]]

    def test_skips_non_messages(self):
        lines = [
            json.dumps({"type": "file-history-snapshot", "messageId": "x", "snapshot": {}, "isSnapshotUpdate": False}),
            _user_msg("hello", uuid="u1"),
            _assistant_text("hi there", uuid="a1", parent="u1"),
        ]
        transcript = "\n".join(lines) + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(transcript)
            f.flush()
            actions = parse_transcript(Path(f.name))

        # Text-only assistant response = turn with empty tool_sequence
        assert len(actions) == 1
        assert actions[0]["tool_sequence"] == []

    def test_approved_field(self):
        """Turns followed by another user message (not interruption) are approved."""
        lines = [
            _user_msg("do something", uuid="u1"),
            _assistant_tool("Read", {"file_path": "/a.md"}, uuid="a1", parent="u1"),
            _tool_result("toolu_1", "ok", uuid="tr1", parent="a1"),
            _assistant_text("Done.", uuid="a2", parent="tr1"),
            _user_msg("thanks", uuid="u2", parent="a2"),
        ]
        transcript = "\n".join(lines) + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(transcript)
            f.flush()
            actions = parse_transcript(Path(f.name))

        assert actions[0]["approved"] is True

    def test_interrupted_not_approved(self):
        lines = [
            _user_msg("do something", uuid="u1"),
            _assistant_tool("Read", {"file_path": "/a.md"}, uuid="a1", parent="u1"),
            _tool_result("toolu_1", "ok", uuid="tr1", parent="a1"),
            # User interrupts
            json.dumps({
                "type": "user", "sessionId": "test-session", "uuid": "u2", "parentUuid": "tr1",
                "timestamp": "2026-03-17T01:02:00Z",
                "message": {"role": "user", "content": [{"type": "text", "text": "[Request interrupted by user]"}]},
            }),
        ]
        transcript = "\n".join(lines) + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(transcript)
            f.flush()
            actions = parse_transcript(Path(f.name))

        assert actions[0]["approved"] is False


# --- extract_actions (integration) ---

class TestExtractActions:
    def test_writes_output_file(self):
        lines = [
            _user_msg("improve post"),
            _assistant_tool("Read", {"file_path": "/posts/union.md"}, uuid="a1", parent="u1"),
            _tool_result("toolu_1", "ok", uuid="tr1", parent="a1"),
        ]
        transcript = "\n".join(lines) + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(transcript)
            f.flush()
            src = Path(f.name)

        with tempfile.TemporaryDirectory() as outdir:
            outpath = Path(outdir)
            extract_actions(src, outpath, session_id="test-session", project="june-kim")
            result_file = outpath / "test-session.jsonl"
            assert result_file.exists()
            records = [json.loads(line) for line in result_file.read_text().strip().split("\n")]
            assert len(records) == 1
            assert records[0]["project"] == "june-kim"
            assert records[0]["session_id"] == "test-session"

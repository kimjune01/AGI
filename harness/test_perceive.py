"""Tests for perceive.py — find repeating tool subsequences across sessions."""

import json
import tempfile
from pathlib import Path

from perceive import (
    find_intent_patterns,
    find_patterns,
    load_actions,
    _tokenize_prompt,
    _intent_signature,
    _compute_idf,
)


def _write_actions(tmpdir: Path, session_id: str, actions: list[dict]) -> Path:
    """Write action records to a JSONL file in tmpdir."""
    outfile = tmpdir / f"{session_id}.jsonl"
    with open(outfile, "w") as f:
        for a in actions:
            f.write(json.dumps(a) + "\n")
    return outfile


def _action(tool_seq: list[list[str]], approved: bool = True, project: str = "test",
            session_id: str = "s1", turn_index: int = 0, prompt: str = "test prompt"):
    return {
        "session_id": session_id,
        "project": project,
        "timestamp": "2026-03-17T01:00:00Z",
        "turn_index": turn_index,
        "prompt_prefix": prompt,
        "tool_sequence": tool_seq,
        "approved": approved,
    }


class TestLoadActions:
    def test_loads_from_dir(self):
        with tempfile.TemporaryDirectory() as d:
            tmpdir = Path(d)
            _write_actions(tmpdir, "s1", [
                _action([["Read", ".md"], ["Edit", ".md"]]),
                _action([["Bash", "git"]]),
            ])
            _write_actions(tmpdir, "s2", [
                _action([["Read", ".py"]], session_id="s2"),
            ])
            actions = load_actions(tmpdir)
            assert len(actions) == 3

    def test_filters_unapproved(self):
        with tempfile.TemporaryDirectory() as d:
            tmpdir = Path(d)
            _write_actions(tmpdir, "s1", [
                _action([["Read", ".md"]], approved=True),
                _action([["Read", ".md"]], approved=False),
            ])
            actions = load_actions(tmpdir, approved_only=True)
            assert len(actions) == 1

    def test_filters_by_project(self):
        with tempfile.TemporaryDirectory() as d:
            tmpdir = Path(d)
            _write_actions(tmpdir, "s1", [
                _action([["Read", ".md"]], project="june-kim"),
                _action([["Read", ".py"]], project="other"),
            ])
            actions = load_actions(tmpdir, project="june-kim")
            assert len(actions) == 1


class TestFindPatterns:
    def test_finds_repeated_sequence(self):
        """Read→Edit→Bash appearing 3+ times should be detected."""
        seq = [["Read", ".md"], ["Edit", ".md"], ["Bash", "git"]]
        actions = [_action(seq, session_id=f"s{i}", turn_index=i) for i in range(5)]

        patterns = find_patterns(actions, min_count=3)
        # The exact sequence should appear
        found = [p for p in patterns if p["sequence"] == [tuple(t) for t in seq]]
        assert len(found) > 0
        assert found[0]["count"] >= 5

    def test_finds_subsequences(self):
        """Read→Edit as a subsequence of Read→Edit→Bash should be found."""
        actions = [
            _action([["Read", ".md"], ["Edit", ".md"], ["Bash", "git"]], session_id="s1"),
            _action([["Read", ".md"], ["Edit", ".md"]], session_id="s2"),
            _action([["Read", ".md"], ["Edit", ".md"], ["Bash", "bundle"]], session_id="s3"),
        ]
        patterns = find_patterns(actions, min_count=2, min_length=2, max_length=3)
        # Read→Edit should appear at least 3 times
        re_pattern = [p for p in patterns if p["sequence"] == [("Read", ".md"), ("Edit", ".md")]]
        assert len(re_pattern) > 0
        assert re_pattern[0]["count"] >= 3

    def test_respects_min_count(self):
        """Sequences appearing fewer than min_count times should not be returned."""
        actions = [
            _action([["Read", ".md"], ["Edit", ".md"]], session_id="s1"),
            _action([["Bash", "npm"]], session_id="s2"),
        ]
        patterns = find_patterns(actions, min_count=3)
        assert len(patterns) == 0

    def test_empty_actions(self):
        patterns = find_patterns([], min_count=1)
        assert patterns == []

    def test_ignores_empty_sequences(self):
        """Actions with empty tool sequences should not contribute patterns."""
        actions = [_action([], session_id=f"s{i}") for i in range(5)]
        patterns = find_patterns(actions, min_count=1, min_length=1)
        assert len(patterns) == 0


# --- Tokenizer tests ---

class TestTokenizePrompt:
    def test_strips_stop_words(self):
        tokens = _tokenize_prompt("improve the post about unions")
        assert "the" not in tokens
        assert "about" not in tokens
        assert "improve" in tokens
        assert "unions" in tokens

    def test_strips_xml_tags(self):
        tokens = _tokenize_prompt("<command-name>/humanize</command-name> run it")
        assert "command-name" not in tokens
        assert "humanize" in tokens or "/humanize" in tokens

    def test_strips_system_noise(self):
        tokens = _tokenize_prompt("[Request interrupted by user]")
        # "request", "interrupted", "user" are all stop words
        assert len(tokens) == 0

    def test_strips_image_refs(self):
        tokens = _tokenize_prompt("[image: source: /var/folders/foo] check this")
        assert "check" in tokens
        assert "source" not in tokens


# --- Intent signature tests ---

class TestIntentSignature:
    def test_picks_high_idf_tokens(self):
        actions = [
            _action([], prompt="improve the blog post"),
            _action([], prompt="improve the blog post"),
            _action([], prompt="deploy kindwatch backend"),
            _action([], prompt="deploy kindwatch backend"),
            _action([], prompt="fix the login bug"),
        ]
        idf = _compute_idf(actions)
        # "kindwatch" appears in 2/5 docs, "improve" in 2/5, "fix" in 1/5
        # "fix" and "login" should have highest IDF
        sig = _intent_signature("fix the login bug", idf, top_k=2)
        assert "login" in sig or "bug" in sig or "fix" in sig

    def test_empty_prompt(self):
        sig = _intent_signature("", {}, top_k=3)
        assert sig == ()


# --- Intent-first pattern finding ---

class TestFindIntentPatterns:
    def test_groups_by_intent(self):
        """Actions with similar prompts should cluster together."""
        actions = (
            [_action([["Read", ".md"], ["Edit", ".md"]],
                     prompt="improve the blog post about unions",
                     session_id=f"s{i}") for i in range(6)]
            + [_action([["Bash", "git"], ["Bash", "git"]],
                       prompt="commit and push changes",
                       session_id=f"t{i}") for i in range(6)]
        )
        patterns = find_intent_patterns(actions, min_count=3)
        assert len(patterns) >= 2
        # Each group should have its own canonical sequence
        sequences = [tuple(tuple(t) for t in p["canonical_sequence"]) for p in patterns]
        assert (("Read", ".md"), ("Edit", ".md")) in sequences
        assert (("Bash", "git"), ("Bash", "git")) in sequences

    def test_respects_min_count(self):
        actions = [
            _action([["Read", ".md"]], prompt="improve blog post", session_id="s1"),
            _action([["Read", ".md"]], prompt="improve blog post", session_id="s2"),
        ]
        patterns = find_intent_patterns(actions, min_count=5)
        assert len(patterns) == 0

    def test_empty_actions(self):
        assert find_intent_patterns([], min_count=1) == []

    def test_tracks_sessions(self):
        actions = [
            _action([["Read", ".md"], ["Edit", ".md"]],
                    prompt="improve blog post",
                    session_id=f"s{i}") for i in range(5)
        ]
        patterns = find_intent_patterns(actions, min_count=3)
        assert len(patterns) >= 1
        assert patterns[0]["sessions"] == 5

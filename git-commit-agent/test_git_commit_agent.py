#!/usr/bin/env python3
"""
Unit tests for git_commit_agent.py

Run with: pytest test_git_commit_agent.py -v
"""

import pytest
from git_commit_agent import (
    parse_tracking_info,
    BranchInfo,
    Config,
    DEFAULT_CONFIG
)


class TestParseTrackingInfo:
    def test_ahead_only(self):
        ahead, behind = parse_tracking_info("[ahead 3]")
        assert ahead == 3
        assert behind == 0

    def test_behind_only(self):
        ahead, behind = parse_tracking_info("[behind 2]")
        assert ahead == 0
        assert behind == 2

    def test_ahead_and_behind(self):
        ahead, behind = parse_tracking_info("[ahead 5, behind 2]")
        assert ahead == 5
        assert behind == 2

    def test_empty_string(self):
        ahead, behind = parse_tracking_info("")
        assert ahead == 0
        assert behind == 0

    def test_no_tracking(self):
        ahead, behind = parse_tracking_info("[]")
        assert ahead == 0
        assert behind == 0

    def test_different_order(self):
        ahead, behind = parse_tracking_info("[behind 1, ahead 4]")
        assert ahead == 4
        assert behind == 1


class TestBranchInfo:
    def test_branch_info_creation(self):
        branch = BranchInfo(
            name="feature/test",
            upstream="origin/main",
            ahead=3,
            behind=0,
            diff_stat="2 files changed, 10 insertions(+), 5 deletions(-)",
            diff_content="diff --git a/test.py...",
            commit_log="abc123 Add feature\ndef456 Fix bug",
            files_changed=2,
            insertions=10,
            deletions=5
        )
        assert branch.name == "feature/test"
        assert branch.upstream == "origin/main"
        assert branch.ahead == 3
        assert branch.files_changed == 2

    def test_branch_info_defaults(self):
        branch = BranchInfo(
            name="main", upstream=None, ahead=0, behind=0,
            diff_stat="", diff_content="", commit_log=""
        )
        assert branch.files_changed == 0
        assert branch.insertions == 0
        assert branch.deletions == 0


class TestConfig:
    def test_config_creation(self):
        config = Config(
            max_diff_chars=50000, model="claude-sonnet-4-5-20250929",
            temperature=0.7, max_retries=3, commit_types=["feat", "fix", "docs"]
        )
        assert config.max_diff_chars == 50000
        assert len(config.commit_types) == 3

    def test_default_config(self):
        config = Config(**DEFAULT_CONFIG)
        assert config.model == "claude-sonnet-4-5-20250929"
        assert "feat" in config.commit_types


class TestDiffTruncation:
    def test_truncation_message(self):
        config = Config(**DEFAULT_CONFIG)
        large_diff = "x" * 100000
        original_size = len(large_diff)
        if len(large_diff) > config.max_diff_chars:
            truncated = large_diff[:config.max_diff_chars]
            truncated += f"\n\n... [Truncated: showing first {config.max_diff_chars} of {original_size} characters]"
        else:
            truncated = large_diff
        assert "Truncated" in truncated

    def test_no_truncation_needed(self):
        config = Config(**DEFAULT_CONFIG)
        small_diff = "x" * 1000
        original_size = len(small_diff)
        if len(small_diff) > config.max_diff_chars:
            truncated = small_diff[:config.max_diff_chars]
            truncated += f"\n\n... [Truncated: showing first {config.max_diff_chars} of {original_size} characters]"
        else:
            truncated = small_diff
        assert len(truncated) == 1000


class TestCommitMessageFormat:
    def test_valid_commit_message_format(self):
        message = """feat(auth): implement JWT authentication\n\n- Add JWT token generation and validation\n- Implement user login endpoint\n- Add password hashing with bcrypt"""
        lines = message.split('\n')
        first_line = lines[0]
        assert '(' in first_line
        assert ')' in first_line
        assert ':' in first_line
        assert len(first_line) <= 72

    def test_commit_type_validation(self):
        config = Config(**DEFAULT_CONFIG)
        valid_types = config.commit_types
        test_messages = [
            "feat(api): add endpoint",
            "fix(auth): resolve bug",
            "docs(readme): update guide",
            "refactor(core): simplify logic"
        ]
        for msg in test_messages:
            commit_type = msg.split('(')[0]
            assert commit_type in valid_types


class TestFileStatisticsParsing:
    def test_parse_files_changed(self):
        import re
        diff_stat = "3 files changed, 42 insertions(+), 15 deletions(-)"
        stat_match = re.search(r'(\d+) files? changed', diff_stat)
        assert int(stat_match.group(1)) == 3

    def test_parse_single_file(self):
        import re
        diff_stat = "1 file changed, 5 insertions(+)"
        stat_match = re.search(r'(\d+) files? changed', diff_stat)
        assert int(stat_match.group(1)) == 1

    def test_parse_no_deletions(self):
        import re
        diff_stat = "2 files changed, 20 insertions(+)"
        delete_match = re.search(r'(\d+) deletions?', diff_stat)
        assert delete_match is None


class TestEdgeCases:
    def test_empty_diff_stat(self):
        import re
        diff_stat = ""
        stat_match = re.search(r'(\d+) files? changed', diff_stat)
        files_changed = int(stat_match.group(1)) if stat_match else 0
        assert files_changed == 0

    def test_branch_with_no_upstream(self):
        branch = BranchInfo(
            name="local-branch", upstream=None, ahead=0, behind=0,
            diff_stat="", diff_content="", commit_log=""
        )
        assert branch.upstream is None

    def test_very_long_branch_name(self):
        long_name = "feature/" + "x" * 200
        branch = BranchInfo(
            name=long_name, upstream="origin/main", ahead=1, behind=0,
            diff_stat="", diff_content="", commit_log=""
        )
        assert len(branch.name) > 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

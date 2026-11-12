"""The standard's acceptance test: this repository's derived set and its
committed configuration are the same thing, hook for hook.
"""

from pathlib import Path

from agent_plugins.lintlint.rules import audit

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestThisRepository:
    def test_this_repository_audits_clean(self) -> None:
        assert audit(REPO_ROOT) == []

"""The typed failures of the checker. Failures raise; an expected absence — a
file with no findings, a configuration not written yet — returns empty instead.

`GitMissing` and `NotARepository` are not findings: they say the checker has no
tracked files to derive from, and every caller degrades rather than guessing.
"""


class LintLintError(Exception):
    """Base of the checker's own failures."""


class GitMissing(LintLintError):
    """`git` is not on the PATH the harness process handed us."""


class NotARepository(LintLintError):
    """The directory is in no git repository."""


class ConfigParseFailed(LintLintError):
    """A file the checker reads does not parse. `message` says why, in one line."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

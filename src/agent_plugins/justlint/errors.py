"""The typed failures of the checker. Failures raise; an expected absence — a
file with no findings, a path with no entrypoint — returns empty instead.

`JustMissing` is not an error of the file under test: it says the checker
cannot run at all, and every caller degrades on it rather than guessing.
"""


class JustLintError(Exception):
    """Base of the checker's own failures."""


class JustMissing(JustLintError):
    """`just` is not on the PATH the harness process handed us."""


class JustParseFailed(JustLintError):
    """`just` refused the file. `message` is the last line it printed."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

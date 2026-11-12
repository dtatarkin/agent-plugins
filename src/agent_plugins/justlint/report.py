"""Rendering findings.

Every line names four things: the recipe (or the file, for a file-level rule),
the rule id, a one-line fix, and the `just-rules` file that states the rule.
The rationale is never repeated — the cited file is the one copy of it.
"""

from collections.abc import Sequence
from pathlib import Path

from agent_plugins.justlint.consts import FILE_SUBJECT, RULES, TOPIC_TEMPLATE
from agent_plugins.justlint.types import Finding


def render_audit(findings: Sequence[Finding], base: Path | None = None) -> str:
    """The audit report: findings grouped by the file they were parsed from."""
    sources = sorted({finding.source for finding in findings})
    blocks: list[str] = []
    for source in sources:
        own = [finding for finding in findings if finding.source == source]
        blocks.append(f"{_display(source, base)}  [{len(own)}]")
        blocks.extend(f"    {_line(finding)}" for finding in own)
    blocks.append(f"{len(findings)} finding(s) in {len(sources)} file(s)")
    return "\n".join(blocks)


def render_context(
    findings: Sequence[Finding], lead: str, limit: int, base: Path | None = None
) -> str:
    """A hook report of at most `limit` characters.

    When the findings do not fit, the report holds as many as do and states how
    many remain, so a large new file is acted on rather than set aside behind a
    preview the model need not open.
    """
    header = f"just-lint: {len(findings)} finding(s) introduced by this context — {lead}"
    lines = [f"  {_display(finding.source, base)}  {_line(finding)}" for finding in findings]
    kept: list[str] = []
    used = len(header)
    for index, line in enumerate(lines):
        remainder = _remainder(len(lines) - index)
        if used + len("\n") + len(line) + len(remainder) > limit:
            kept.append(remainder)
            break
        kept.append(line)
        used += len("\n") + len(line)
    return "\n".join([header, *kept])


def _remainder(count: int) -> str:
    return f"  … and {count} more — run `just-lint check` for the rest"


def _line(finding: Finding) -> str:
    rule = RULES[finding.rule]
    subject = finding.subject or FILE_SUBJECT
    detail = f"{finding.detail}; " if finding.detail else ""
    topic = TOPIC_TEMPLATE.format(topic=rule.topic)
    return f"{subject}  {finding.rule.value}: {detail}{rule.fix}  ({topic})"


def _display(source: Path, base: Path | None) -> str:
    """`source` as seen from `base` (the working directory when unset), or in
    full when it lies outside it.
    """
    try:
        return str(source.relative_to(base or Path.cwd()))
    except ValueError:
        return str(source)

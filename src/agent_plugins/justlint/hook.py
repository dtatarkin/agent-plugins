"""`just-lint hook` — the in-session half: a ratchet and one Stop gate.

The sequence per justfile, within one context:

- **PreToolUse** of an Edit or a Write records the file's findings as the
  baseline, once. The file is still unedited at that point, and a file being
  created does not exist yet, so it gets an empty baseline.
- **PostToolUse** reports the findings absent from that baseline and stays
  silent when there are none. Findings after the edit, never before it:
  context handed to PreToolUse reaches the model only after the call it
  precedes was already composed.
- **Stop** and **SubagentStop** block once per prompt while introduced
  findings remain.

Everything here is standard library: the path runs on every governed edit and
at every turn end, and a `typer` import there would be paid each time. It also
fails open — a broken checker costs feedback, never a tool call.
"""

import json
import sys
from pathlib import Path

from agent_plugins.justlint.checker import file_findings, keys_of
from agent_plugins.justlint.consts import INLINE_LIMIT
from agent_plugins.justlint.errors import JustMissing
from agent_plugins.justlint.report import render_context
from agent_plugins.justlint.resolve import is_checked_file
from agent_plugins.justlint.state import LintState, prune, state_root
from agent_plugins.justlint.types import Finding, FindingKey, JsonObject

POST_LEAD = "fix them now, before moving on"
STOP_LEAD = "still open; fix them before finishing"
NO_JUST_NOTICE = "just-lint: `just` is not on PATH, so justfile checks are off in this session."

# Marker names. The `just` notice is stated once per context; the Stop gate is
# keyed on the prompt, never on `stop_hook_active` — that flag is also true
# after another hook's block, which would skip this gate silently.
NO_JUST_MARKER = "no-just"
BLOCKED_MARKER = "blocked-{prompt}"


def run_hook() -> int:
    """Read one hook payload from stdin and write the harness's answer, if any,
    to stdout. Diagnostics go to stderr, which a successful hook keeps out of
    the model's context.
    """
    try:
        payload: JsonObject = json.load(sys.stdin)
        answer = handle(payload)
    except Exception as failure:  # a hook never fails the tool call it watches
        print(f"just-lint: {failure}", file=sys.stderr)
        return 0
    if answer is not None:
        json.dump(answer, sys.stdout)
    return 0


def handle(payload: JsonObject) -> JsonObject | None:
    """The answer to one hook event, or `None` to stay silent."""
    event = payload.get("hook_event_name")
    state = LintState.for_context(payload.get("session_id") or "", payload.get("agent_id"))
    if event == "PreToolUse":
        return _pre_tool_use(payload, state)
    if event == "PostToolUse":
        return _post_tool_use(payload, state)
    if event in ("Stop", "SubagentStop"):
        return _stop(payload, state)
    return None


def _pre_tool_use(payload: JsonObject, state: LintState) -> JsonObject | None:
    """Record the baseline, once per file and context. Nothing is ever handed
    back: context given to PreToolUse reaches the model only after the call it
    precedes was composed, so findings wait for PostToolUse.
    """
    path = _edited_path(payload)
    if path is None or state.baseline(path) is not None:
        return None
    try:
        state.record_baseline(path, keys_of(file_findings(path)))
    except JustMissing:
        return None  # nothing to measure against; the notice follows the edit
    return None


def _post_tool_use(payload: JsonObject, state: LintState) -> JsonObject | None:
    """Report what this edit introduced, and nothing else."""
    path = _edited_path(payload)
    if path is None:
        return None
    try:
        current = file_findings(path)
    except JustMissing:
        return _context(NO_JUST_NOTICE) if state.claim(NO_JUST_MARKER) else None
    baseline = state.baseline(path)
    if baseline is None:
        # PreToolUse did not run for this file, so nothing says which findings
        # predate the context. Adopt the current ones rather than blame the
        # edit for a file's history.
        state.record_baseline(path, keys_of(current))
        return None
    introduced = _introduced(current, baseline)
    if not introduced:
        return None
    return _context(render_context(introduced, POST_LEAD, INLINE_LIMIT, _cwd(payload)))


def _stop(payload: JsonObject, state: LintState) -> JsonObject | None:
    """Block once per prompt while findings this context introduced remain."""
    prune(state_root())
    if not state.exists:
        return None
    try:
        pending = [
            finding
            for path, baseline in state.tracked()
            for finding in _introduced(file_findings(path), baseline)
        ]
    except JustMissing:
        return None
    if not pending:
        return None
    prompt = payload.get("prompt_id") or "unknown"
    if not state.claim(BLOCKED_MARKER.format(prompt=prompt)):
        return None
    reason = render_context(pending, STOP_LEAD, INLINE_LIMIT, _cwd(payload))
    return {"decision": "block", "reason": reason}


def _introduced(current: list[Finding], baseline: set[FindingKey]) -> list[Finding]:
    """The findings absent from the baseline. A renamed recipe counts as new,
    because the key names the recipe.
    """
    return [finding for finding in current if finding.key not in baseline]


def _edited_path(payload: JsonObject) -> Path | None:
    """The file an Edit or a Write names, when the checker acts on that name.

    The filter is re-applied here rather than trusted to the hook's `if`: an
    over-firing filter must not make the checker dump an unrelated file.
    """
    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return None
    path = Path(file_path)
    return path if is_checked_file(path) else None


def _cwd(payload: JsonObject) -> Path | None:
    cwd = payload.get("cwd")
    return Path(cwd) if isinstance(cwd, str) and cwd else None


def _context(text: str) -> JsonObject:
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}

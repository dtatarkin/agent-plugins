"""The mechanically checkable rules, read off one parsed unit.

A *unit* is one dump node: the entrypoint, or a module `just` loaded with
`mod`. Imports carry no node of their own — `just` merges them into the
importing unit — so an imported fragment's recipes are checked where they land.

Formatting is not checked here and must not be added: `just --fmt` output
moves between `just` releases, and this checker runs on the machine's `just`
while a repository's formatter hook pins its own. Judgment rules — reusing the
shared modules, grouping, preferring dependency calls to `just …` bodies,
`[no-cd]` placement, `mod?`/`import?` — have no check either; they reach the
agent through the rule files.
"""

from collections.abc import Iterator
from pathlib import Path

from agent_plugins.justlint.consts import MODULE_SUFFIX
from agent_plugins.justlint.types import Finding, JsonObject, RuleId

# The nested-shell commands whose quoted argument a splat may sit in: each hands
# that string to a fresh shell, which re-splits it, so a variadic inside one is
# the plain-tokens-only form the conventions sanction rather than a splat into
# this shell's text. An allowlist, not a general quote analysis.
#
# `sops exec-env` is the second family, and `sops-exec-env` catches a project
# recipe of that name wrapping it (`just sops-exec-env <file> '<command>'`),
# which is how the estate actually spells it.
NESTED_SHELL_COMMANDS = ("git submodule foreach", "sops exec-env", "sops-exec-env")

# What an interpolation contributes when the literal text around it is read.
# Anything without a quote of its own would do.
INTERPOLATION_PLACEHOLDER = "{{}}"

# `set -euo pipefail` belongs directly under the shebang, so only the opening
# lines of a body are searched for it.
STRICT_PREAMBLE_LINES = 3


def check_unit(unit: JsonObject, *, is_entrypoint: bool) -> list[Finding]:
    """Every finding of one parsed unit, sorted by recipe then rule."""
    source = Path(unit["source"])
    findings = list(_check_preamble(source, unit, is_entrypoint=is_entrypoint))
    for name, recipe in unit["recipes"].items():
        findings.extend(_check_recipe(source, name, recipe))
    return sorted(findings)


def _check_preamble(source: Path, unit: JsonObject, *, is_entrypoint: bool) -> Iterator[Finding]:
    """`module-preamble`, which applies to `*.just` files loaded with `mod`.

    An entrypoint is exempt, and so is a sub-repository's `justfile` that an
    umbrella loads with `mod`: it is its own repository's entrypoint, and it is
    excluded here by its name rather than by its role.
    """
    if is_entrypoint or source.suffix != MODULE_SUFFIX:
        return
    missing = []
    if "source_file" not in unit["assignments"]:
        missing.append("no `source_file := source_file()`")
    if "list" not in unit["recipes"]:
        missing.append("no `list` recipe")
    if missing:
        yield Finding(source, "", RuleId.MODULE_PREAMBLE, " and ".join(missing))


def _check_recipe(source: Path, name: str, recipe: JsonObject) -> Iterator[Finding]:
    attributes = recipe["attributes"]
    has_doc = any(isinstance(a, dict) and "doc" in a for a in attributes)
    marked_private = any(a == "private" for a in attributes if isinstance(a, str))
    underscored = name.startswith("_")
    # `just` reports `private` for both halves of the convention, so the two
    # directions of `private-prefix` are told apart by the name and the
    # attribute, never by this flag.
    private = bool(recipe["private"]) or underscored

    if not private and not has_doc:
        yield Finding(
            source,
            name,
            RuleId.DOC_ATTR,
            "bare-comment help" if recipe["doc"] else "no help at all",
        )
    if private and has_doc:
        yield Finding(source, name, RuleId.PRIVATE_DOC)
    if underscored and not marked_private:
        yield Finding(source, name, RuleId.PRIVATE_PREFIX, "`_` name without [private]")
    if marked_private and not underscored:
        yield Finding(source, name, RuleId.PRIVATE_PREFIX, "[private] without a `_` name")

    splatted = _splatted_variadics(recipe)
    if splatted:
        yield Finding(source, name, RuleId.SPLAT, "{{ " + ", ".join(splatted) + " }} in the body")

    body: list[list[object]] = recipe["body"]
    if not recipe["shebang"] and len(body) > 1:
        yield Finding(source, name, RuleId.SHEBANG, f"{len(body)}-line body")
    if recipe["shebang"] and body and _is_bash_shebang(body[0]) and not _is_strict(body):
        yield Finding(source, name, RuleId.STRICT)


def _splatted_variadics(recipe: JsonObject) -> list[str]:
    """The variadic parameters this recipe interpolates into its body.

    One finding per recipe however many parameters it splats: the ratchet keys
    on the recipe and the rule, and a second name is a detail of the same
    violation.
    """
    variadic = {p["name"] for p in recipe["parameters"] if p["kind"] in ("star", "plus")}
    if not variadic:
        return []
    found: set[str] = set()
    for line in recipe["body"]:
        for index, fragment in enumerate(line):
            if isinstance(fragment, str):
                continue
            names = _interpolated_names(fragment) & variadic
            if names and not _opens_nested_shell(_literal_text(line[:index])):
                found |= names
    return sorted(found)


def _interpolated_names(fragment: object) -> set[str]:
    """The variable names an interpolation reads, at any depth.

    `just` renders an interpolation as a token tree — `[["variable", "args"]]`,
    `[["call", "module_file"]]` — so the walk looks for the pair rather than a
    fixed shape.
    """
    names: set[str] = set()
    if isinstance(fragment, list):
        if len(fragment) == 2 and fragment[0] == "variable" and isinstance(fragment[1], str):
            names.add(fragment[1])
        for item in fragment:
            names |= _interpolated_names(item)
    return names


def _opens_nested_shell(prefix: str) -> bool:
    """True when `prefix` leaves a quoted argument of an allowlisted
    nested-shell command open, so the interpolation after it is re-evaluated by
    the shell that command starts rather than by this one.

    Either quote character opens such an argument: `git submodule foreach` is
    written with double quotes and the `sops exec-env` forms with single ones,
    and an odd count after the command name is what says it is still open.
    """
    for command in NESTED_SHELL_COMMANDS:
        start = prefix.rfind(command)
        if start < 0:
            continue
        if any(prefix.count(quote, start) % 2 == 1 for quote in ('"', "'")):
            return True
    return False


def _literal_text(fragments: list[object]) -> str:
    """The literal text of body-line fragments, interpolations stood in for."""
    return "".join(f if isinstance(f, str) else INTERPOLATION_PLACEHOLDER for f in fragments)


def _is_bash_shebang(line: list[object]) -> bool:
    text = _literal_text(line)
    return text.startswith("#!") and "bash" in text


def _is_strict(body: list[list[object]]) -> bool:
    return any("set -euo pipefail" in _literal_text(line) for line in body[:STRICT_PREAMBLE_LINES])

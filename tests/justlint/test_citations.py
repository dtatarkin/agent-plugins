"""Guards the citation every finding carries — the rule file that states it.

A finding names a rule id, a one-line fix, and the `just-rules` topic file
holding the rationale, which is the only copy of it. Nothing resolves that
citation at runtime: the checker formats a path and the agent goes looking, so
a renamed topic, or a rule quietly dropped from a file it still cites, leaves
findings pointing at text that no longer says what they claim. The four cited
files were split out of one document in a single change — exactly when such a
pointer rots. This test is what notices.

Existence is the cheap half. The substantive half is that the file still
*states* the rule, so the evidence below is scoped: the tokens of one rule must
meet inside one block, because a token found anywhere in the file proves
nothing when every topic file repeats the same few `just` tokens.
"""

from pathlib import Path

import pytest

from agent_plugins.justlint.consts import RULES, TOPIC_TEMPLATE
from agent_plugins.justlint.types import RuleId

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = REPO_ROOT / "plugins" / "just-rules"

# One marker is a set of tokens that must co-occur in a single block; a rule is
# stated only when every one of its markers is met. Tokens are the `just`
# syntax the rule mandates or forbids wherever that discriminates — syntax
# cannot be reworded without changing the rule itself — plus, where two rules
# share a file and the same syntax, the one prose word that separates them
# (`help`, `strict`, `shebang`, `parse`). Prose otherwise stays out: these files
# are rewritten often, and a marker that pins a sentence would fail on a reflow.
Marker = tuple[str, ...]
EVIDENCE: dict[RuleId, tuple[Marker, ...]] = {
    # The attribute, tied to what `just --list` shows: the ordering bullet names
    # `[doc("…")]` too, but never the listing.
    RuleId.DOC_ATTR: (("[doc(", "just --list"),),
    # The same two attributes as the ordering bullet, plus the help text a
    # private recipe must not carry.
    RuleId.PRIVATE_DOC: (("[private]", "[doc(", "help"),),
    # The pairing itself: a leading `_` and the attribute, in one breath.
    RuleId.PRIVATE_PREFIX: (("[private]", "_"),),
    # The word and the line. A neighbouring example carries the line alone.
    RuleId.SHEBANG: (("shebang", "#!/usr/bin/env bash"),),
    # Strict mode rides in the shebang bullet, so the line alone is not enough.
    RuleId.STRICT: (("strict", "set -euo pipefail"),),
    # What to do, and the splat it replaces — the refinement bullets below it
    # show the shape but never the anti-pattern.
    RuleId.SPLAT: (("[positional-arguments]", '"$@"', "{{ args }}"),),
    # Both halves of the preamble, each free to be stated in its own block.
    RuleId.MODULE_PREAMBLE: (("source_file := source_file()",), ("just::list",)),
    # The optional forms and the reason they exist.
    RuleId.PARSE: (("mod?", "parse"),),
}


def _normalize(text: str) -> str:
    """Lowercased, backticks and emphasis dropped, whitespace collapsed.

    Rewrapping a paragraph, bolding a lead-in or fencing an example must not
    move a token out of reach — only the token itself is evidence.
    """
    return " ".join(text.replace("`", "").replace("*", "").lower().split())


def _blocks(text: str) -> list[str]:
    """The file split into rule statements: every top-level `- ` bullet with its
    continuation, and whatever prose or example stands outside one.

    A rule is stated by one bullet — or, for a module's preamble, by the example
    block above them — so this is the scope a marker must be met in.
    """
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("- "):
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    blocks.append("\n".join(current))
    return [_normalize(block) for block in blocks]


def citation_violations(rule: RuleId, topic: str, plugin_dir: Path) -> list[str]:
    """Violations of one rule id's citation; empty when the file states the rule."""
    citation = TOPIC_TEMPLATE.format(topic=topic)
    path = plugin_dir / citation
    if not path.is_file():
        return [f"{rule.value} cites {citation}, which the plugin does not ship"]

    blocks = _blocks(path.read_text())
    return [
        f"{rule.value}: {citation} states no rule holding {' + '.join(marker)}"
        for marker in EVIDENCE[rule]
        if not any(all(token in block for token in marker) for block in blocks)
    ]


class TestEveryCitation:
    def test_the_evidence_covers_the_checker_table(self) -> None:
        """Keeps the parametrized test below from passing vacuously.

        An emptied table would parametrize to nothing; a rule id added to the
        checker without evidence here would go uncited and unnoticed.
        """
        assert set(RULES) == set(RuleId), "the checker's table has lost a rule id"
        assert set(EVIDENCE) == set(RULES), "a rule id in the checker's table has no evidence here"

    @pytest.mark.parametrize("rule", RULES, ids=lambda rule: rule.value)
    def test_cites_a_file_that_states_the_rule(self, rule: RuleId) -> None:
        assert citation_violations(rule, RULES[rule].topic, PLUGIN_DIR) == []


# `recipes.md` as it might read after the shebang rule was dropped: both of that
# rule's tokens survive — the word in one bullet, the line in another bullet's
# example — so only the block scope catches the loss.
DROPPED_SHEBANG = """\
# Recipes

- **Help text via `[doc("…")]`, always.** Every recipe in `just --list` carries one.
- **Separate a rationale comment from the recipe with one blank line.**

  ```just
  # why this exists

  [doc("Run it")]
  run:
      #!/usr/bin/env bash
  ```

- **Don't hand-order attributes.** `just --fmt` sorts them, a shebang body included.
"""

# The same file with the rule back in one piece.
KEPT_SHEBANG = """\
# Recipes

- **Help text via `[doc("…")]`, always.** Every recipe in `just --list` carries one.
- **Shebang body for multi-line shell.** Without a shebang each line gets its own shell.

  ```just
  [doc("Run it")]
  run:
      #!/usr/bin/env bash
  ```
"""


def _plugin(tmp_path: Path, topic: str, text: str) -> Path:
    """A stand-in plugin directory shipping one topic file."""
    path = tmp_path / TOPIC_TEMPLATE.format(topic=topic)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return tmp_path


class TestRejections:
    def test_a_citation_to_a_file_that_is_not_there(self, tmp_path: Path) -> None:
        assert citation_violations(RuleId.SHEBANG, "recipes", tmp_path) == [
            "shebang cites skills/just/references/recipes.md, which the plugin does not ship"
        ]

    def test_a_renamed_topic(self, tmp_path: Path) -> None:
        plugin = _plugin(tmp_path, "bodies", KEPT_SHEBANG)
        assert citation_violations(RuleId.SHEBANG, "recipes", plugin) == [
            "shebang cites skills/just/references/recipes.md, which the plugin does not ship"
        ]

    def test_a_file_that_no_longer_states_the_rule(self, tmp_path: Path) -> None:
        plugin = _plugin(tmp_path, "recipes", DROPPED_SHEBANG)
        assert citation_violations(RuleId.SHEBANG, "recipes", plugin) == [
            "shebang: skills/just/references/recipes.md states no rule holding "
            "shebang + #!/usr/bin/env bash"
        ]

    def test_one_half_of_a_two_part_rule(self, tmp_path: Path) -> None:
        plugin = _plugin(tmp_path, "modules", "- Always assign `source_file := source_file()`.\n")
        assert citation_violations(RuleId.MODULE_PREAMBLE, "modules", plugin) == [
            "module-preamble: skills/just/references/modules.md states no rule holding just::list"
        ]

    def test_a_file_that_states_it(self, tmp_path: Path) -> None:
        plugin = _plugin(tmp_path, "recipes", KEPT_SHEBANG)
        assert citation_violations(RuleId.SHEBANG, "recipes", plugin) == []

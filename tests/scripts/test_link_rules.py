"""Tests for `scripts/link-rules`, the opt-in linking of scoped rule files.

Each test runs the copy of the script the `link_setup` fixture places in a
throwaway repository. The last test runs the real script over the real tree,
into a throwaway configuration directory.
"""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures.scripts.link_rules import (
    NO_FRONTMATTER,
    SCOPED,
    SCRIPT,
    Setup,
    run_script,
)
from tests.plugins.test_rule_frontmatter import declares_paths, shape_violations

REPO_ROOT = Path(__file__).resolve().parents[2]

ALPHA_LINKS = {"alpha-rules--one.md", "alpha-rules--two.md"}
BETA_LINKS = {"beta-rules--three.md"}
ALL_LINKS = ALPHA_LINKS | BETA_LINKS


def entries(directory: Path) -> set[str]:
    return {entry.name for entry in directory.iterdir()}


def linked(result: subprocess.CompletedProcess[str], verb: str = "linked") -> set[str]:
    lines = result.stdout.splitlines()
    assert all(line.startswith(f"{verb} ") for line in lines), result.stdout
    return {line.removeprefix(f"{verb} ") for line in lines}


def snapshot(directory: Path) -> dict[str, str]:
    """Every entry: a link by its literal target, a file by its content."""
    return {
        entry.name: f"link:{os.readlink(entry)}"
        if entry.is_symlink()
        else f"file:{entry.read_text()}"
        for entry in directory.iterdir()
    }


# A shim run first on PATH as `python3`: the real interpreter, reporting 3.11,
# running the script as `__main__`.
OLD_PYTHON_SHIM = """#!/bin/sh
exec {python} -c '
import runpy, sys
sys.version_info = (3, 11, 0, "final", 0)
script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
' "$@"
"""


EDGE_CASES = {
    "no-frontmatter": "# Rules\n",
    "no-paths": "---\ntitle: x\n---\n",
    "paths-after-close": "---\ntitle: x\n---\npaths: x\n",
    "paths-then-key": '---\npaths:\n  - "x"\ntitle: y\n---\n',
    "indented-paths": '---\n  paths:\n    - "x"\n---\n',
    "crlf": '---\r\npaths:\r\n  - "x"\r\n---\r\n',
    "trailing-space": '--- \npaths:\n  - "x"\n---\n',
    "unclosed": '---\npaths:\n  - "x"\n',
    "canonical": '---\npaths:\n  - "x"\n---\n',
}


class TestLinking:
    """The script links every scoped rule file."""

    def test_first_run(self, link_setup: Setup) -> None:
        assert not link_setup.rules.exists()

        result = link_setup.run()

        assert result.returncode == 0, result.stderr
        assert entries(link_setup.rules) == ALL_LINKS
        assert linked(result) == ALL_LINKS
        for name in ALL_LINKS:
            plugin, topic = name.removesuffix(".md").split("--")
            link = link_setup.rules / name
            assert link.is_symlink()
            assert os.readlink(link) == str(link_setup.rule_file(plugin, topic))
            assert link.samefile(link_setup.rule_file(plugin, topic))

    def test_an_unscoped_rule_file(self, link_setup: Setup) -> None:
        link_setup.run()

        names = entries(link_setup.rules)
        assert "alpha-rules--plain.md" not in names
        assert "beta-rules--titled.md" not in names

    def test_the_configuration_directory_is_moved(self, link_setup: Setup) -> None:
        result = link_setup.run()

        assert result.returncode == 0, result.stderr
        assert entries(link_setup.rules) == ALL_LINKS
        assert not (link_setup.home / ".claude").exists()

    def test_home_alone_links_under_dot_claude(self, link_setup: Setup) -> None:
        result = link_setup.run(env={"HOME": str(link_setup.home)})

        assert result.returncode == 0, result.stderr
        assert entries(link_setup.home / ".claude" / "rules") == ALL_LINKS
        assert not link_setup.config.exists()

    def test_the_clone_is_updated(self, link_setup: Setup) -> None:
        link_setup.run()
        changed = SCOPED + "\nA new paragraph.\n"
        link_setup.rule_file("alpha-rules", "one").write_text(changed)

        assert (link_setup.rules / "alpha-rules--one.md").read_text() == changed


class TestNarrowing:
    """Plugin names narrow the selection."""

    def test_one_plugin_named(self, link_setup: Setup) -> None:
        result = link_setup.run("alpha-rules")

        assert result.returncode == 0, result.stderr
        assert entries(link_setup.rules) == ALPHA_LINKS
        assert linked(result) == ALPHA_LINKS

    @pytest.mark.parametrize("argument", ["gamma-rules", "alpha-rules/skills", ".."])
    def test_an_unknown_plugin_named(self, link_setup: Setup, argument: str) -> None:
        link_setup.run("beta-rules")
        before = snapshot(link_setup.rules)

        result = link_setup.run("alpha-rules", argument)

        assert result.returncode == 2
        assert argument in result.stderr
        assert result.stdout == ""
        assert snapshot(link_setup.rules) == before

    def test_an_unknown_plugin_named_creates_nothing(self, link_setup: Setup) -> None:
        result = link_setup.run("gamma-rules")

        assert result.returncode == 2
        assert not link_setup.config.exists()


class TestRerun:
    """A re-run converges and prunes only its own links."""

    def test_nothing_changed(self, link_setup: Setup) -> None:
        link_setup.run()
        before = snapshot(link_setup.rules)

        result = link_setup.run()

        assert result.returncode == 0, result.stderr
        assert result.stdout == ""
        assert result.stderr == ""
        assert snapshot(link_setup.rules) == before

    def test_a_rule_file_is_removed_or_unscoped(self, link_setup: Setup) -> None:
        link_setup.run()
        link_setup.rule_file("alpha-rules", "one").unlink()
        link_setup.rule_file("beta-rules", "three").write_text(NO_FRONTMATTER)

        result = link_setup.run()

        assert result.returncode == 0, result.stderr
        assert linked(result, "unlinked") == {"alpha-rules--one.md", "beta-rules--three.md"}
        assert entries(link_setup.rules) == {"alpha-rules--two.md"}

    def test_foreign_entries_are_left_alone(self, link_setup: Setup, tmp_path: Path) -> None:
        link_setup.rules.mkdir(parents=True)
        elsewhere = tmp_path / "elsewhere.md"
        elsewhere.write_text("elsewhere\n")
        (link_setup.rules / "mine.md").write_text("a user's own rule\n")
        (link_setup.rules / "theirs.md").symlink_to(elsewhere)
        (link_setup.rules / "dangling.md").symlink_to(tmp_path / "gone.md")
        foreign = snapshot(link_setup.rules)

        for args in [(), ("alpha-rules",), ("--unlink",)]:
            result = link_setup.run(*args)
            assert result.returncode == 0, result.stderr
            current = snapshot(link_setup.rules)
            assert {name: current[name] for name in foreign} == foreign

    def test_a_narrowed_run_keeps_other_plugins_links(self, link_setup: Setup) -> None:
        link_setup.run()
        before = snapshot(link_setup.rules)

        result = link_setup.run("alpha-rules")

        assert result.returncode == 0, result.stderr
        assert result.stdout == ""
        assert snapshot(link_setup.rules) == before


class TestOwnership:
    """The script never replaces what it does not own."""

    def test_a_regular_file_holds_the_name(self, link_setup: Setup) -> None:
        link_setup.rules.mkdir(parents=True)
        held = link_setup.rules / "alpha-rules--one.md"
        held.write_text("a user's own rule\n")

        result = link_setup.run()

        assert result.returncode == 1
        assert "alpha-rules--one.md" in result.stderr
        assert not held.is_symlink()
        assert held.read_text() == "a user's own rule\n"
        assert linked(result) == ALL_LINKS - {"alpha-rules--one.md"}
        assert entries(link_setup.rules) == ALL_LINKS

    @pytest.mark.parametrize("target_exists", [True, False])
    def test_a_foreign_link_holds_the_name(
        self, link_setup: Setup, tmp_path: Path, target_exists: bool
    ) -> None:
        link_setup.rules.mkdir(parents=True)
        target = tmp_path / "another-tool" / "one.md"
        if target_exists:
            target.parent.mkdir()
            target.write_text("another tool's rule\n")
        held = link_setup.rules / "alpha-rules--one.md"
        held.symlink_to(target)

        result = link_setup.run()

        assert result.returncode == 1
        assert "alpha-rules--one.md" in result.stderr
        assert str(target) in result.stderr
        assert os.readlink(held) == str(target)
        assert linked(result) == ALL_LINKS - {"alpha-rules--one.md"}

    def test_a_foreign_link_already_resolves_to_the_file(
        self, link_setup: Setup, tmp_path: Path
    ) -> None:
        # The same file reached through another path: not the script's own prefix.
        alias = tmp_path.resolve() / "alias"
        alias.symlink_to(link_setup.repo)
        link_setup.rules.mkdir(parents=True)
        held = link_setup.rules / "alpha-rules--one.md"
        foreign_target = alias / link_setup.rule_file("alpha-rules", "one").relative_to(
            link_setup.repo
        )
        held.symlink_to(foreign_target)

        result = link_setup.run()

        assert result.returncode == 0, result.stderr
        assert result.stderr == ""
        assert os.readlink(held) == str(foreign_target)
        assert linked(result) == ALL_LINKS - {"alpha-rules--one.md"}

        # Done, so --unlink does not take it either.
        link_setup.run("--unlink")
        assert os.readlink(held) == str(foreign_target)


class TestUnlink:
    """Unlink removes only the script's own links."""

    def test_opting_out(self, link_setup: Setup, tmp_path: Path) -> None:
        link_setup.run()
        (link_setup.rules / "mine.md").write_text("a user's own rule\n")
        (link_setup.rules / "theirs.md").symlink_to(tmp_path / "elsewhere.md")

        result = link_setup.run("--unlink")

        assert result.returncode == 0, result.stderr
        assert linked(result, "unlinked") == ALL_LINKS
        assert entries(link_setup.rules) == {"mine.md", "theirs.md"}

    def test_opting_out_of_one_plugin(self, link_setup: Setup) -> None:
        link_setup.run()

        result = link_setup.run("--unlink", "alpha-rules")

        assert result.returncode == 0, result.stderr
        assert linked(result, "unlinked") == ALPHA_LINKS
        assert entries(link_setup.rules) == BETA_LINKS

    def test_unlink_without_a_rules_directory(self, link_setup: Setup) -> None:
        result = link_setup.run("--unlink")

        assert result.returncode == 0, result.stderr
        assert not link_setup.config.exists()


class TestOptIn:
    """Linking is opt-in and Claude Code only."""

    def test_a_plugin_is_installed(self) -> None:
        """No plugin ships the script and nothing in a plugin invokes it."""
        plugins = REPO_ROOT / "plugins"
        shipped = [path for path in plugins.rglob("*") if path.name == "link-rules"]
        assert shipped == []
        invoking = [
            path
            for path in plugins.rglob("*")
            if path.is_file() and "link-rules" in path.read_text(errors="replace")
        ]
        assert invoking == []


class TestInterpreter:
    def test_the_interpreter_is_too_old(self, link_setup: Setup, tmp_path: Path) -> None:
        shim_dir = tmp_path / "shim"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text(OLD_PYTHON_SHIM.format(python=sys.executable))
        shim.chmod(0o755)

        result = link_setup.run(
            env={
                "PATH": f"{shim_dir}{os.pathsep}{os.environ['PATH']}",
                "HOME": str(link_setup.home),
                "CLAUDE_CONFIG_DIR": str(link_setup.config),
            }
        )

        assert result.returncode == 2
        assert result.stderr == "link-rules: needs python3 3.12 or later\n"
        assert result.stdout == ""
        assert not link_setup.config.exists()

    def test_the_script_parses_as_python_39(self) -> None:
        """An older python3 must reach the version check, not a syntax error."""
        ast.parse(SCRIPT.read_text(), filename=str(SCRIPT), feature_version=(3, 9))


class TestArguments:
    @pytest.mark.parametrize("args", [("--bogus",), ("alpha-rules", "--unlink"), ("-x",)])
    def test_an_unknown_option(self, link_setup: Setup, args: tuple[str, ...]) -> None:
        result = link_setup.run(*args)

        assert result.returncode == 2
        assert not link_setup.config.exists()

    @pytest.mark.parametrize("flag", ["-h", "--help"])
    def test_help(self, link_setup: Setup, flag: str) -> None:
        result = link_setup.run(flag)

        assert result.returncode == 0
        assert result.stdout.startswith("usage: link-rules")
        assert not link_setup.config.exists()


class TestDetection:
    """The script's line-based detection agrees with the contract's YAML reading on
    every file the contract's shape check passes.
    """

    @pytest.mark.parametrize("case", sorted(EDGE_CASES))
    def test_detection_agrees_with_the_contract(self, link_setup: Setup, case: str) -> None:
        text = EDGE_CASES[case]
        path = link_setup.rule_file("edge-rules", case)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode())

        result = link_setup.run("edge-rules")

        assert result.returncode == 0, result.stderr
        script_links = linked(result) == {f"edge-rules--{case}.md"}
        if shape_violations(text):
            return  # the contract test fails the file before it can be committed
        assert script_links == declares_paths(text)


class TestRealTree:
    def test_the_real_tree(self, tmp_path: Path) -> None:
        config = tmp_path / "config"
        home = tmp_path / "home"
        home.mkdir()

        result = run_script(SCRIPT, env={"HOME": str(home), "CLAUDE_CONFIG_DIR": str(config)})

        assert result.returncode == 0, result.stderr
        links = list((config / "rules").iterdir())
        assert links
        scoped = [
            path
            for path in REPO_ROOT.glob("plugins/*/skills/*/references/*.md")
            if declares_paths(path.read_text())
        ]
        for link in links:
            assert link.is_symlink()
            assert any(os.path.samefile(link, path) for path in scoped), link
        assert len(links) == len(scoped)

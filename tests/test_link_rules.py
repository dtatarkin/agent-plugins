"""Tests for `scripts/link-rules`, the opt-in linking of scoped rule files.

Each test runs a copy of the script inside a throwaway repository under
`tmp_path`, with `HOME` and `CLAUDE_CONFIG_DIR` pointed at throwaway
directories, so the real rules directory is never touched. The last test runs
the real script over the real tree, into a throwaway configuration directory.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.plugins.test_rule_frontmatter import declares_paths

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "link-rules"

SCOPED = "---\npaths:\n  - '**/*.alpha'\n---\n\n# A scoped topic\n"
NO_FRONTMATTER = "# An unscoped topic\n"
NO_PATHS = "---\ntitle: unscoped\n---\n\n# Frontmatter without paths\n"

# The tree the fixture builds: plugin -> topic -> content.
TREE = {
    "alpha-rules": {"one": SCOPED, "two": SCOPED, "plain": NO_FRONTMATTER},
    "beta-rules": {"three": SCOPED, "titled": NO_PATHS},
}
ALPHA_LINKS = {"alpha-rules--one.md", "alpha-rules--two.md"}
BETA_LINKS = {"beta-rules--three.md"}
ALL_LINKS = ALPHA_LINKS | BETA_LINKS


@dataclass
class Setup:
    repo: Path
    home: Path
    config: Path

    @property
    def rules(self) -> Path:
        return self.config / "rules"

    def rule_file(self, plugin: str, topic: str) -> Path:
        return self.repo / "plugins" / plugin / "skills" / "topics" / "references" / f"{topic}.md"

    def run(
        self, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        if env is None:
            env = {"HOME": str(self.home), "CLAUDE_CONFIG_DIR": str(self.config)}
        return run_script(self.repo / "scripts" / "link-rules", *args, env=env)


def run_script(script: Path, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(script), *args],
        env={"PATH": os.environ["PATH"], **env},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def setup(tmp_path: Path) -> Setup:
    # Resolved, because the script writes physical targets.
    base = tmp_path.resolve()
    repo = base / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy2(SCRIPT, repo / "scripts" / "link-rules")
    built = Setup(repo=repo, home=base / "home", config=base / "config")
    for plugin, topics in TREE.items():
        for topic, content in topics.items():
            path = built.rule_file(plugin, topic)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    built.home.mkdir()
    return built


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


# The script links every scoped rule file.


def test_first_run(setup: Setup) -> None:
    assert not setup.rules.exists()

    result = setup.run()

    assert result.returncode == 0, result.stderr
    assert entries(setup.rules) == ALL_LINKS
    assert linked(result) == ALL_LINKS
    for name in ALL_LINKS:
        plugin, topic = name.removesuffix(".md").split("--")
        link = setup.rules / name
        assert link.is_symlink()
        assert os.readlink(link) == str(setup.rule_file(plugin, topic))
        assert link.samefile(setup.rule_file(plugin, topic))


def test_an_unscoped_rule_file(setup: Setup) -> None:
    setup.run()

    names = entries(setup.rules)
    assert "alpha-rules--plain.md" not in names
    assert "beta-rules--titled.md" not in names


def test_the_configuration_directory_is_moved(setup: Setup) -> None:
    result = setup.run()

    assert result.returncode == 0, result.stderr
    assert entries(setup.rules) == ALL_LINKS
    assert not (setup.home / ".claude").exists()


def test_home_alone_links_under_dot_claude(setup: Setup) -> None:
    result = setup.run(env={"HOME": str(setup.home)})

    assert result.returncode == 0, result.stderr
    assert entries(setup.home / ".claude" / "rules") == ALL_LINKS
    assert not setup.config.exists()


def test_the_clone_is_updated(setup: Setup) -> None:
    setup.run()
    changed = SCOPED + "\nA new paragraph.\n"
    setup.rule_file("alpha-rules", "one").write_text(changed)

    assert (setup.rules / "alpha-rules--one.md").read_text() == changed


# Plugin names narrow the selection.


def test_one_plugin_named(setup: Setup) -> None:
    result = setup.run("alpha-rules")

    assert result.returncode == 0, result.stderr
    assert entries(setup.rules) == ALPHA_LINKS
    assert linked(result) == ALPHA_LINKS


@pytest.mark.parametrize("argument", ["gamma-rules", "alpha-rules/skills", ".."])
def test_an_unknown_plugin_named(setup: Setup, argument: str) -> None:
    setup.run("beta-rules")
    before = snapshot(setup.rules)

    result = setup.run("alpha-rules", argument)

    assert result.returncode == 2
    assert argument in result.stderr
    assert result.stdout == ""
    assert snapshot(setup.rules) == before


def test_an_unknown_plugin_named_creates_nothing(setup: Setup) -> None:
    result = setup.run("gamma-rules")

    assert result.returncode == 2
    assert not setup.config.exists()


# A re-run converges and prunes only its own links.


def test_nothing_changed(setup: Setup) -> None:
    setup.run()
    before = snapshot(setup.rules)

    result = setup.run()

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""
    assert snapshot(setup.rules) == before


def test_a_rule_file_is_removed_or_unscoped(setup: Setup) -> None:
    setup.run()
    setup.rule_file("alpha-rules", "one").unlink()
    setup.rule_file("beta-rules", "three").write_text(NO_FRONTMATTER)

    result = setup.run()

    assert result.returncode == 0, result.stderr
    assert linked(result, "unlinked") == {"alpha-rules--one.md", "beta-rules--three.md"}
    assert entries(setup.rules) == {"alpha-rules--two.md"}


def test_foreign_entries_are_left_alone(setup: Setup, tmp_path: Path) -> None:
    setup.rules.mkdir(parents=True)
    elsewhere = tmp_path / "elsewhere.md"
    elsewhere.write_text("elsewhere\n")
    (setup.rules / "mine.md").write_text("a user's own rule\n")
    (setup.rules / "theirs.md").symlink_to(elsewhere)
    (setup.rules / "dangling.md").symlink_to(tmp_path / "gone.md")
    foreign = snapshot(setup.rules)

    for args in [(), ("alpha-rules",), ("--unlink",)]:
        result = setup.run(*args)
        assert result.returncode == 0, result.stderr
        current = snapshot(setup.rules)
        assert {name: current[name] for name in foreign} == foreign


def test_a_narrowed_run_keeps_other_plugins_links(setup: Setup) -> None:
    setup.run()
    before = snapshot(setup.rules)

    result = setup.run("alpha-rules")

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert snapshot(setup.rules) == before


# The script never replaces what it does not own.


def test_a_regular_file_holds_the_name(setup: Setup) -> None:
    setup.rules.mkdir(parents=True)
    held = setup.rules / "alpha-rules--one.md"
    held.write_text("a user's own rule\n")

    result = setup.run()

    assert result.returncode == 1
    assert "alpha-rules--one.md" in result.stderr
    assert not held.is_symlink()
    assert held.read_text() == "a user's own rule\n"
    assert linked(result) == ALL_LINKS - {"alpha-rules--one.md"}
    assert entries(setup.rules) == ALL_LINKS


@pytest.mark.parametrize("target_exists", [True, False])
def test_a_foreign_link_holds_the_name(setup: Setup, tmp_path: Path, target_exists: bool) -> None:
    setup.rules.mkdir(parents=True)
    target = tmp_path / "another-tool" / "one.md"
    if target_exists:
        target.parent.mkdir()
        target.write_text("another tool's rule\n")
    held = setup.rules / "alpha-rules--one.md"
    held.symlink_to(target)

    result = setup.run()

    assert result.returncode == 1
    assert "alpha-rules--one.md" in result.stderr
    assert str(target) in result.stderr
    assert os.readlink(held) == str(target)
    assert linked(result) == ALL_LINKS - {"alpha-rules--one.md"}


def test_a_foreign_link_already_resolves_to_the_file(setup: Setup, tmp_path: Path) -> None:
    # The same file reached through another path: not the script's own prefix.
    alias = tmp_path.resolve() / "alias"
    alias.symlink_to(setup.repo)
    setup.rules.mkdir(parents=True)
    held = setup.rules / "alpha-rules--one.md"
    foreign_target = alias / setup.rule_file("alpha-rules", "one").relative_to(setup.repo)
    held.symlink_to(foreign_target)

    result = setup.run()

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert os.readlink(held) == str(foreign_target)
    assert linked(result) == ALL_LINKS - {"alpha-rules--one.md"}

    # Done, so --unlink does not take it either.
    setup.run("--unlink")
    assert os.readlink(held) == str(foreign_target)


# Unlink removes only the script's own links.


def test_opting_out(setup: Setup, tmp_path: Path) -> None:
    setup.run()
    (setup.rules / "mine.md").write_text("a user's own rule\n")
    (setup.rules / "theirs.md").symlink_to(tmp_path / "elsewhere.md")

    result = setup.run("--unlink")

    assert result.returncode == 0, result.stderr
    assert linked(result, "unlinked") == ALL_LINKS
    assert entries(setup.rules) == {"mine.md", "theirs.md"}


def test_opting_out_of_one_plugin(setup: Setup) -> None:
    setup.run()

    result = setup.run("--unlink", "alpha-rules")

    assert result.returncode == 0, result.stderr
    assert linked(result, "unlinked") == ALPHA_LINKS
    assert entries(setup.rules) == BETA_LINKS


def test_unlink_without_a_rules_directory(setup: Setup) -> None:
    result = setup.run("--unlink")

    assert result.returncode == 0, result.stderr
    assert not setup.config.exists()


# Linking is opt-in and Claude Code only.


def test_a_plugin_is_installed() -> None:
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


# Arguments.


@pytest.mark.parametrize("args", [("--bogus",), ("alpha-rules", "--unlink"), ("-x",)])
def test_an_unknown_option(setup: Setup, args: tuple[str, ...]) -> None:
    result = setup.run(*args)

    assert result.returncode == 2
    assert not setup.config.exists()


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help(setup: Setup, flag: str) -> None:
    result = setup.run(flag)

    assert result.returncode == 0
    assert result.stdout.startswith("usage: link-rules")
    assert not setup.config.exists()


# The real tree.


def test_the_real_tree(tmp_path: Path) -> None:
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

"""The derivation: each row of the signal table, from tracked files alone."""

from collections.abc import Callable
from pathlib import Path

import pytest

from agent_plugins.lintlint.errors import NotARepository
from agent_plugins.lintlint.signals import derive, find_repository
from agent_plugins.lintlint.types import Signal, Signals

Tree = Callable[..., Path]


def signals_of(root: Path) -> Signals:
    return derive(find_repository(root))


@pytest.mark.parametrize(
    ("path", "signal"),
    [
        ("pyproject.toml", Signal.PYTHON),
        ("scripts/tool.py", Signal.PYTHON),
        ("config.yaml", Signal.MARKUP),
        ("config.yml", Signal.MARKUP),
        ("taplo.toml", Signal.MARKUP),
        ("README.md", Signal.MARKUP),
        ("scripts/run.sh", Signal.SHELL),
        ("anywhere/at/all/main.tf", Signal.TERRAFORM),
        ("anywhere/at/all/main.tf", Signal.SCANNED),
        ("ansible/site.yml", Signal.ANSIBLE),
        ("ansible/site.yml", Signal.SCANNED),
        ("galaxy.yml", Signal.ANSIBLE),
        ("galaxy.yml", Signal.SCANNED),
        ("roles/web/tasks/main.yml", Signal.ANSIBLE),
        ("roles/web/tasks/main.yml", Signal.SCANNED),
        ("Dockerfile", Signal.DOCKERFILE),
        ("deploy/Dockerfile.worker", Signal.DOCKERFILE),
        ("deploy/app.dockerfile", Signal.DOCKERFILE),
        ("chart/Chart.yaml", Signal.SCANNED),
        ("analytics/dbt_project.yml", Signal.DATA),
    ],
)
def test_a_tracked_file_carries_its_signal(lint_tree: Tree, path: str, signal: Signal) -> None:
    assert signal in signals_of(lint_tree({path: ""})).present


def test_an_empty_repository_carries_the_baseline_alone(lint_tree: Tree) -> None:
    assert signals_of(lint_tree({})).present == {Signal.ALWAYS}


def test_a_terraform_file_derives_the_trio_and_the_pair_alone(lint_tree: Tree) -> None:
    present = signals_of(lint_tree({"main.tf": ""})).present
    assert present == {Signal.ALWAYS, Signal.TERRAFORM, Signal.SCANNED}


def test_ansible_content_derives_its_linter_and_the_pair_alone(lint_tree: Tree) -> None:
    present = signals_of(lint_tree({"ansible/site.yml": ""})).present
    assert present == {Signal.ALWAYS, Signal.MARKUP, Signal.ANSIBLE, Signal.SCANNED}


@pytest.mark.parametrize("path", ["compose.yaml", "deploy/docker-compose.dev.yml"])
def test_a_compose_file_derives_no_scanner(lint_tree: Tree, path: str) -> None:
    assert signals_of(lint_tree({path: ""})).present == {Signal.ALWAYS, Signal.MARKUP}


def test_an_ansible_directory_of_notes_is_not_ansible_content(lint_tree: Tree) -> None:
    assert Signal.ANSIBLE not in signals_of(lint_tree({"docs/ansible/notes.txt": ""})).present


class TestManifests:
    def test_a_kubernetes_manifest_is_a_scanned_signal(self, lint_tree: Tree) -> None:
        tree = lint_tree({"deploy/app.yaml": "apiVersion: v1\nkind: Service\n"})
        assert Signal.SCANNED in signals_of(tree).present

    def test_a_yaml_file_with_one_of_the_keys_is_not_one(self, lint_tree: Tree) -> None:
        tree = lint_tree({"deploy/app.yaml": "kind: Service\nspec:\n  apiVersion: v1\n"})
        assert Signal.SCANNED not in signals_of(tree).present


class TestShebang:
    def test_an_executable_script_carries_the_shell_signal(self, lint_tree: Tree) -> None:
        tree = lint_tree({"bin/run": "#!/usr/bin/env bash\n"}, executable=["bin/run"])
        assert Signal.SHELL in signals_of(tree).present

    def test_an_absolute_interpreter_does_too(self, lint_tree: Tree) -> None:
        tree = lint_tree({"bin/run": "#!/bin/sh\n"}, executable=["bin/run"])
        assert Signal.SHELL in signals_of(tree).present

    def test_another_interpreter_does_not(self, lint_tree: Tree) -> None:
        tree = lint_tree({"bin/run": "#!/usr/bin/env python3\n"}, executable=["bin/run"])
        assert Signal.SHELL not in signals_of(tree).present

    def test_a_script_that_is_not_executable_is_not_read(self, lint_tree: Tree) -> None:
        tree = lint_tree({"bin/run": "#!/usr/bin/env bash\n"})
        assert Signal.SHELL not in signals_of(tree).present


class TestLockfiles:
    def test_a_tracked_lockfile_at_the_root(self, lint_tree: Tree) -> None:
        signals = signals_of(lint_tree({"uv.lock": ""}))
        assert Signal.PYTHON_LOCK in signals.present
        assert signals.tracks_lockfile

    def test_a_lockfile_deeper_in_is_not_the_repository_s_own(self, lint_tree: Tree) -> None:
        assert Signal.PYTHON_LOCK not in signals_of(lint_tree({"tools/uv.lock": ""})).present

    def test_an_untracked_lockfile_does_not_count(self, lint_tree: Tree) -> None:
        tree = lint_tree({"README.md": ""})
        (tree / "uv.lock").write_text("")
        assert Signal.PYTHON_LOCK not in signals_of(tree).present

    def test_a_lockfile_above_the_repository_does_not_count(self, lint_tree: Tree) -> None:
        tree = lint_tree({"inner/README.md": "", "inner/NESTED_REPO": ""}, "outer", repo=False)
        (tree / "uv.lock").write_text("")
        (tree / "inner" / "NESTED_REPO").unlink()
        inner = lint_tree({"README.md": ""}, "outer/inner")
        assert Signal.PYTHON_LOCK not in signals_of(inner).present


class TestWeb:
    @pytest.mark.parametrize(
        ("lockfile", "executor"),
        [("pnpm-lock.yaml", "pnpm"), ("package-lock.json", "npm"), ("yarn.lock", "yarn")],
    )
    def test_a_manifest_beside_a_lockfile(
        self, lint_tree: Tree, lockfile: str, executor: str
    ) -> None:
        tree = lint_tree(
            {"web/package.json": "{}", f"web/{lockfile}": "", "web/src/app/main.ts": ""}
        )
        signals = signals_of(tree)
        assert Signal.WEB in signals.present
        assert signals.executors == {executor}

    @pytest.mark.parametrize(
        "source", ["main.ts", "a.tsx", "a.mts", "a.cts", "a.js", "a.jsx", "a.mjs", "a.cjs"]
    )
    def test_every_web_source_suffix(self, lint_tree: Tree, source: str) -> None:
        tree = lint_tree({"package.json": "{}", "pnpm-lock.yaml": "", f"src/{source}": ""})
        assert Signal.WEB in signals_of(tree).present

    def test_a_manifest_with_no_web_source_derives_nothing(self, lint_tree: Tree) -> None:
        signals = signals_of(lint_tree({"package.json": "{}", "package-lock.json": ""}))
        assert Signal.WEB not in signals.present
        assert signals.executors == frozenset()
        assert signals.tracks_lockfile

    def test_a_source_the_top_level_exclusion_matches_is_not_web_source(
        self, lint_tree: Tree
    ) -> None:
        tree = lint_tree(
            {"package.json": "{}", "pnpm-lock.yaml": "", "static/vendor/htmx.min.js": ""}
        )
        signals = derive(find_repository(tree), "^static/vendor/")
        assert Signal.WEB not in signals.present
        assert signals.tracks_lockfile

    def test_a_source_outside_the_manifest_s_directory_is_not_either(self, lint_tree: Tree) -> None:
        tree = lint_tree({"web/package.json": "{}", "web/pnpm-lock.yaml": "", "other/main.ts": ""})
        assert Signal.WEB not in signals_of(tree).present

    def test_stylesheets_and_templates_are_not_web_source(self, lint_tree: Tree) -> None:
        tree = lint_tree(
            {
                "package.json": "{}",
                "pnpm-lock.yaml": "",
                "templates/index.html": "",
                "static/site.css": "",
            }
        )
        assert Signal.WEB not in signals_of(tree).present

    def test_a_manifest_alone_is_not_the_signal(self, lint_tree: Tree) -> None:
        tree = lint_tree({"package.json": "{}", "main.ts": ""})
        assert Signal.WEB not in signals_of(tree).present

    def test_a_lockfile_in_another_directory_is_not_either(self, lint_tree: Tree) -> None:
        tree = lint_tree({"package.json": "{}", "other/pnpm-lock.yaml": "", "main.ts": ""})
        assert Signal.WEB not in signals_of(tree).present


PORTABLE = '{"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": "a"}'
MANIFEST_SIGNALS = {Signal.CLAUDE_MANIFEST, Signal.PORTABLE_MANIFEST}


class TestPluginManifests:
    @pytest.mark.parametrize(
        "path",
        [
            ".claude-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
            "plugins/a/.claude-plugin/plugin.json",
        ],
    )
    def test_a_claude_manifest_carries_its_signal(self, lint_tree: Tree, path: str) -> None:
        present = signals_of(lint_tree({path: "{}"})).present
        assert present & MANIFEST_SIGNALS == {Signal.CLAUDE_MANIFEST}

    @pytest.mark.parametrize("path", ["plugin.json", "plugins/a/plugin.json"])
    def test_a_portable_manifest_carries_its_signal(self, lint_tree: Tree, path: str) -> None:
        present = signals_of(lint_tree({path: PORTABLE})).present
        assert present & MANIFEST_SIGNALS == {Signal.PORTABLE_MANIFEST}

    def test_another_schema_version_is_the_same_signal(self, lint_tree: Tree) -> None:
        manifest = PORTABLE.replace("1.0.0", "2.1.0")
        assert Signal.PORTABLE_MANIFEST in signals_of(lint_tree({"plugin.json": manifest})).present

    @pytest.mark.parametrize(
        "text",
        [
            '{"name": "a"}',
            '{"$schema": "https://json.schemastore.org/package.json"}',
            '{"$schema": 1}',
            '["https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"]',
            "{not json",
            "",
        ],
    )
    def test_a_plugin_json_without_the_schema_carries_none(
        self, lint_tree: Tree, text: str
    ) -> None:
        assert not signals_of(lint_tree({"plugin.json": text})).present & MANIFEST_SIGNALS

    def test_a_schema_declaring_manifest_under_the_claude_directory_is_claude_s(
        self, lint_tree: Tree
    ) -> None:
        present = signals_of(lint_tree({".claude-plugin/plugin.json": PORTABLE})).present
        assert present & MANIFEST_SIGNALS == {Signal.CLAUDE_MANIFEST}

    @pytest.mark.parametrize(
        "path",
        [
            ".agents/plugins/marketplace.json",
            "action.yml",
            ".github/dependabot.yml",
            "docs/.claude-plugin/settings.json",
            ".claude-plugin/nested/plugin.json",
        ],
    )
    def test_other_files_carry_none(self, lint_tree: Tree, path: str) -> None:
        assert not signals_of(lint_tree({path: "{}"})).present & MANIFEST_SIGNALS


class TestWorkflows:
    @pytest.mark.parametrize("path", [".github/workflows/ci.yml", ".github/workflows/release.yaml"])
    def test_a_workflow_carries_the_signal(self, lint_tree: Tree, path: str) -> None:
        assert Signal.WORKFLOWS in signals_of(lint_tree({path: "on: push\n"})).present

    @pytest.mark.parametrize(
        "path",
        [
            ".github/workflows/nested/ci.yml",
            ".github/workflows/README.md",
            "action.yml",
            ".github/actions/setup/action.yml",
            ".github/dependabot.yml",
            "sub/.github/workflows/ci.yml",
        ],
    )
    def test_other_files_do_not(self, lint_tree: Tree, path: str) -> None:
        assert Signal.WORKFLOWS not in signals_of(lint_tree({path: "on: push\n"})).present


class TestExcludedFiles:
    def test_a_file_every_hook_excludes_carries_no_content_signal(self, lint_tree: Tree) -> None:
        tree = lint_tree({"vendor/lib/Dockerfile": "", "vendor/lib/main.tf": ""})
        present = derive(find_repository(tree), "^vendor/").present
        assert present == {Signal.ALWAYS}

    def test_a_tracked_lockfile_stands_regardless(self, lint_tree: Tree) -> None:
        tree = lint_tree({"uv.lock": ""})
        assert Signal.PYTHON_LOCK in derive(find_repository(tree), r"\.lock$").present

    def test_a_pattern_the_runner_would_refuse_excludes_nothing(self, lint_tree: Tree) -> None:
        tree = lint_tree({"main.tf": ""})
        assert Signal.TERRAFORM in derive(find_repository(tree), "(").present


class TestBoundary:
    def test_an_untracked_script_contributes_nothing(self, lint_tree: Tree) -> None:
        tree = lint_tree({"README.md": ""})
        (tree / ".venv" / "bin").mkdir(parents=True)
        (tree / ".venv" / "bin" / "activate.sh").write_text("")
        assert Signal.SHELL not in signals_of(tree).present

    def test_a_nested_repository_derives_nothing_above_it(
        self, lint_data_tree: Callable[[str], Path]
    ) -> None:
        tree = lint_data_tree("umbrella")
        assert Signal.TERRAFORM not in signals_of(tree).present
        assert Signal.TERRAFORM in signals_of(tree / "sub").present

    def test_the_repository_holding_a_subdirectory_is_found(self, lint_tree: Tree) -> None:
        tree = lint_tree({"deep/er/README.md": ""})
        assert find_repository(tree / "deep" / "er").root == tree

    def test_a_directory_outside_any_repository(self, lint_tree: Tree) -> None:
        with pytest.raises(NotARepository):
            find_repository(lint_tree({"README.md": ""}, repo=False))

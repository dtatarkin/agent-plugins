"""One test per scenario of the two "enforced" requirements and of "What belongs
to the project is not checked". Each starts from the compliant tree and changes
the one thing the scenario names.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from agent_plugins.lintlint.rules import audit, is_governed
from agent_plugins.lintlint.types import Finding, RuleId
from tests.fixtures.lintlint.scenarios import CONFIG, WEB_HOOKS, add_local_hooks, edit
from tests.fixtures.lintlint.trees import track

Tree = Callable[[str], Path]


def pairs(findings: list[Finding]) -> set[tuple[str, str]]:
    return {(f.subject, f.rule.value) for f in findings}


ANSIBLE_HOOKS = """\
      - id: ansible-lint
        entry: uv run ansible-lint --offline
        language: system
        files: ^ansible/
        require_serial: true
        pass_filenames: false
      - id: checkov
        entry: uv run checkov --quiet --directory ansible
        language: system
        files: ^ansible/
        pass_filenames: false
      - id: trivy-config
        entry: trivy config --exit-code 1 --severity HIGH,CRITICAL ansible
        language: system
        files: ^ansible/
        pass_filenames: false
"""


class TestCompliantTree:
    def test_the_compliant_tree_is_clean(self, lint_data_tree: Path) -> None:
        assert audit(lint_data_tree) == []


class TestTheHookSet:
    def test_a_hook_of_the_set_is_absent(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "      - id: validate-pyproject\n", "      - id: project-drift\n")
        assert pairs(audit(lint_data_tree)) == {("validate-pyproject", "missing-hook")}

    def test_a_missing_hook_cites_its_set_s_topic(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "      - id: validate-pyproject\n", "      - id: project-drift\n")
        assert audit(lint_data_tree)[0].topic == "python"

    def test_a_markup_tree_without_the_link_checker(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "      - id: lychee\n", "      - id: link-drift\n")
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("lychee", "missing-hook")}
        assert findings[0].topic == "markup"

    def test_three_dropped_hygiene_ids_are_three_findings(self, lint_data_tree: Path) -> None:
        for hook in ("check-json", "check-symlinks", "debug-statements"):
            edit(lint_data_tree, f"      - id: {hook}\n", "")
        assert pairs(audit(lint_data_tree)) == {
            ("check-json", "missing-hook"),
            ("check-symlinks", "missing-hook"),
            ("debug-statements", "missing-hook"),
        }

    def test_a_hook_outlives_its_signal(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            "  - repo: local\n",
            "  - repo: https://github.com/shellcheck-py/shellcheck-py\n"
            "    rev: v0.11.0.1-1\n    hooks:\n      - id: shellcheck\n\n  - repo: local\n",
        )
        assert pairs(audit(lint_data_tree)) == {("shellcheck", "stray-hook")}

    def test_the_lockfile_hooks_leave_with_the_lockfile(self, lint_data_tree: Path) -> None:
        (lint_data_tree / "uv.lock").unlink()
        track(lint_data_tree, {})
        found = pairs(audit(lint_data_tree))
        assert ("uv-lock", "stray-hook") in found
        assert ("pip-audit", "stray-hook") in found

    def test_a_terraform_file_derives_the_trio_and_the_pair(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, {"anywhere/main.tf": ""})
        assert pairs(audit(lint_data_tree)) == {
            ("terraform-fmt", "missing-hook"),
            ("terraform-validate", "missing-hook"),
            ("tflint", "missing-hook"),
            ("checkov", "missing-hook"),
            ("trivy-config", "missing-hook"),
        }

    def test_ansible_content_derives_its_linter_and_the_pair(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, {"ansible/site.yml": ""})
        found = pairs(audit(lint_data_tree))
        assert {hook for hook, rule in found if rule == "missing-hook"} == {
            "ansible-lint",
            "checkov",
            "trivy-config",
        }

    def test_ansible_content_and_both_scanners_report_no_stray_hook(
        self, lint_data_tree: Path
    ) -> None:
        track(lint_data_tree, {"ansible/site.yml": ""})
        add_local_hooks(lint_data_tree, ANSIBLE_HOOKS)
        assert {f.rule for f in audit(lint_data_tree)} == {RuleId.CONFIG_VALUE}

    def test_a_manifest_with_no_web_source_strays_the_web_hooks(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, {"package.json": "{}", "pnpm-lock.yaml": ""})
        add_local_hooks(lint_data_tree, WEB_HOOKS)
        assert pairs(audit(lint_data_tree)) == {
            ("eslint", "stray-hook"),
            ("prettier", "stray-hook"),
            ("typecheck", "stray-hook"),
        }

    def test_a_dockerfile_derives_its_linter_alone(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, {"Dockerfile": ""})
        assert pairs(audit(lint_data_tree)) == {("hadolint", "missing-hook")}


class TestRetiredTools:
    @pytest.mark.parametrize(
        ("repo", "hook", "house_tool"),
        [
            ("https://github.com/codespell-project/codespell", "codespell", "typos"),
            ("https://github.com/PyCQA/bandit", "bandit", "security rules"),
            ("https://github.com/pre-commit/mirrors-mypy", "mypy", "mypy"),
            ("https://github.com/instrumentl/pre-commit-just", "format-justfile", "format-just"),
            ("https://github.com/pypa/pip-audit", "pip-audit", "pip-audit"),
            ("https://github.com/hadolint/hadolint", "hadolint-docker", "hadolint"),
            ("https://github.com/astral-sh/ruff-pre-commit", "ruff", "ruff-check"),
        ],
    )
    def test_a_retired_hook_names_the_house_tool(
        self, lint_data_tree: Path, repo: str, hook: str, house_tool: str
    ) -> None:
        edit(
            lint_data_tree,
            "  - repo: local\n",
            f"  - repo: {repo}\n    rev: v1.2.3\n    hooks:\n      - id: {hook}\n\n"
            "  - repo: local\n",
        )
        retired = [f for f in audit(lint_data_tree) if f.rule is RuleId.RETIRED_TOOL]
        assert [f.subject for f in retired] == [hook]
        assert house_tool in retired[0].detail

    def test_a_retired_tool_inside_a_local_entry(self, lint_data_tree: Path) -> None:
        add_local_hooks(
            lint_data_tree,
            "      - id: format-docs\n        entry: npx dprint fmt\n        language: system\n",
        )
        assert pairs(audit(lint_data_tree)) == {("format-docs", "retired-tool")}

    def test_a_formatter_pinned_inside_an_entry(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "uv run just --fmt", "uvx --from rust-just==1.40 just --fmt")
        assert ("format-justfile", "retired-tool") in pairs(audit(lint_data_tree))

    def test_a_code_formatter_pointed_at_markup(self, web_tree: Path) -> None:
        edit(
            web_tree, "types_or: [ts, tsx, javascript, jsx, css, html]", "types_or: [ts, markdown]"
        )
        assert pairs(audit(web_tree)) == {("prettier", "retired-tool")}


class TestCanonicalArguments:
    @pytest.mark.parametrize(
        ("old", "new", "hook", "named"),
        [
            ("args: [--strict]\n", "args: []\n", "yamllint", "--strict"),
            ("        types_or: [python, pyi, jupyter]\n", "", "ruff-format", "types_or"),
            ("        args: [--fix=lf]\n", "", "mixed-line-ending", "--fix=lf"),
            ("rumdl-check\n        args: [--fix]\n", "rumdl-check\n", "rumdl-check", "--fix"),
            (", --offline, --no-progress]", ", --no-progress]", "lychee", "--offline"),
            (", --offline, --no-progress]", ", --offline]", "lychee", "--no-progress"),
        ],
    )
    def test_the_argument_is_named(
        self, lint_data_tree: Path, old: str, new: str, hook: str, named: str
    ) -> None:
        edit(lint_data_tree, old, new)
        findings = audit(lint_data_tree)
        assert pairs(findings) == {(hook, "hook-args")}
        assert named in findings[0].detail

    @pytest.mark.parametrize(
        "args",
        [
            "[--offline, --no-progress]",
            "[--offline, LYCHEE_VERSION=0.24.2, --no-progress]",
        ],
    )
    def test_the_link_checker_without_its_version_first(
        self, lint_data_tree: Path, args: str
    ) -> None:
        edit(lint_data_tree, "[LYCHEE_VERSION=0.24.2, --offline, --no-progress]", args)
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("lychee", "hook-args")}
        assert "`LYCHEE_VERSION=0.24.2` is not the first argument" in findings[0].detail

    def test_a_stale_link_checker_version_names_both(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "LYCHEE_VERSION=0.24.2", "LYCHEE_VERSION=0.23.0")
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("lychee", "hook-args")}
        assert "0.23.0" in findings[0].detail
        assert "lychee-v0.24.2" in findings[0].detail

    def test_a_link_checker_pin_without_its_tag_prefix_asks_only_for_an_override(
        self, lint_data_tree: Path
    ) -> None:
        edit(lint_data_tree, "rev: lychee-v0.24.2", "rev: v0.15.1")
        assert audit(lint_data_tree) == []
        edit(lint_data_tree, "[LYCHEE_VERSION=0.24.2, ", "[")
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("lychee", "hook-args")}
        assert "`LYCHEE_VERSION=<version>`" in findings[0].detail

    def test_a_local_link_checker_is_the_projects(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            "https://github.com/lycheeverse/lychee\n    rev: lychee-v0.24.2",
            "local",
        )
        edit(
            lint_data_tree,
            "[LYCHEE_VERSION=0.24.2, --offline, --no-progress]\n",
            "[--offline, --no-progress]\n        entry: lychee\n        language: system\n",
        )
        assert audit(lint_data_tree) == []

    def test_the_second_scanner_without_its_exit_code(self, terraform_tree: Path) -> None:
        edit(terraform_tree, "--exit-code 1 ", "")
        findings = audit(terraform_tree)
        assert pairs(findings) == {("trivy-config", "hook-args")}
        assert "--exit-code 1" in findings[0].detail

    def test_either_spelling_of_a_flag_and_value_is_one(self, terraform_tree: Path) -> None:
        edit(terraform_tree, "--exit-code 1 ", "--exit-code=1 ")
        assert audit(terraform_tree) == []

    def test_a_longer_flag_does_not_stand_in(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            "      - id: yamllint\n        args: [--strict]",
            "      - id: yamllint\n        args: [--strict-mode]",
        )
        assert pairs(audit(lint_data_tree)) == {("yamllint", "hook-args")}

    def test_the_spelling_checker_keeps_its_defaults(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            "      - id: typos\n",
            "      - id: typos\n        args: [--locale, en-gb]\n",
        )
        assert pairs(audit(lint_data_tree)) == {("typos", "hook-args")}

    def test_the_spelling_checker_with_its_defaults_repeated(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            "      - id: typos\n",
            "      - id: typos\n"
            "        args: [--write-changes, --force-exclude, --locale, en-gb]\n",
        )
        assert audit(lint_data_tree) == []

    def test_the_validator_keeps_its_manifest_dependencies(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            "      - id: validate-pyproject\n",
            "      - id: validate-pyproject\n        additional_dependencies: [packaging]\n",
        )
        assert pairs(audit(lint_data_tree)) == {("validate-pyproject", "hook-args")}

    def test_a_filter_on_the_secret_scan_does_nothing(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            "      - id: gitleaks\n",
            "      - id: gitleaks\n        exclude: ^tests/\n",
        )
        assert pairs(audit(lint_data_tree)) == {("gitleaks", "hook-args")}

    def test_the_parse_check_may_take_its_unsafe_flag(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            "      - id: check-yaml\n",
            "      - id: check-yaml\n        args: [--unsafe]\n",
        )
        assert audit(lint_data_tree) == []


MYPY = "entry: uv run mypy\n        language: system\n        types: [python]\n"
ESLINT = "--fix\n        language: system\n        types_or: [ts, tsx, javascript, jsx]\n"


class TestWholeProgramChecks:
    def test_a_type_checker_handed_the_file_list(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            f"{MYPY}        pass_filenames: false\n",
            MYPY,
        )
        assert pairs(audit(lint_data_tree)) == {("mypy", "hook-args")}

    def test_a_type_checker_with_no_filter(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            MYPY,
            "entry: uv run mypy\n        language: system\n",
        )
        assert pairs(audit(lint_data_tree)) == {("mypy", "hook-args")}

    @pytest.mark.parametrize("hook", ["tflint", "checkov", "trivy-config", "terraform-fmt"])
    def test_a_scanner_or_terraform_hook(self, terraform_tree: Path, hook: str) -> None:
        text = (terraform_tree / CONFIG).read_text()
        head, tail = text.split(f"      - id: {hook}\n")
        (terraform_tree / CONFIG).write_text(
            f"{head}      - id: {hook}\n{tail.replace('        pass_filenames: false\n', '', 1)}"
        )
        assert pairs(audit(terraform_tree)) == {(hook, "hook-args")}

    def test_a_web_type_check(self, web_tree: Path) -> None:
        edit(
            web_tree,
            "types_or: [ts, tsx]\n        pass_filenames: false\n",
            "types_or: [ts, tsx]\n",
        )
        assert pairs(audit(web_tree)) == {("typecheck", "hook-args")}

    def test_a_rewriting_web_hook_runs_serially(self, web_tree: Path) -> None:
        edit(
            web_tree,
            f"{ESLINT}        require_serial: true\n",
            ESLINT,
        )
        assert pairs(audit(web_tree)) == {("eslint", "hook-args")}


class TestStages:
    def test_a_network_check_blocks(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "        stages: [manual]\n", "")
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("pip-audit", "hook-args")}
        assert "manual" in findings[0].detail

    def test_the_audit_exports_the_workspace_flag(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "--no-emit-workspace", "--no-emit-project")
        assert pairs(audit(lint_data_tree)) == {("pip-audit", "hook-args")}


SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"

PLUGIN_MANIFESTS = {
    "plugins/a/plugin.json": f'{{"$schema": "{SCHEMA_URL}", "name": "a"}}',
    "plugins/a/.claude-plugin/plugin.json": '{"name": "a"}',
}

SCHEMA_CHECK = f"""
  - repo: https://github.com/python-jsonschema/check-jsonschema
    rev: 0.39.0
    hooks:
      - id: check-jsonschema
        args: [--schemafile, {SCHEMA_URL}]
        files: (^|/)plugin\\.json$
        exclude: (^|/)\\.claude-plugin/
        stages: [manual]
"""

# The schema check's stage, apart from the dependency audit's.
MANUAL_STAGE = "        stages: [manual]\n"
SCHEMA_STAGE = "\\.claude-plugin/\n" + MANUAL_STAGE

CLAUDE_VALIDATE = """\
      - id: claude-plugin-validate
        name: claude plugin validate
        entry: bash -c 'for f in "$@"; do claude plugin validate --strict "$f" || exit 1; done' --
        language: system
        files: (^|/)\\.claude-plugin/(plugin|marketplace)\\.json$
"""


def add_plugin_hooks(tree: Path) -> None:
    add_local_hooks(tree, CLAUDE_VALIDATE)
    with (tree / CONFIG).open("a") as stream:
        stream.write(SCHEMA_CHECK)


class TestAgentPlugins:
    @pytest.fixture
    def plugin_tree(self, lint_data_tree: Path) -> Path:
        track(lint_data_tree, PLUGIN_MANIFESTS)
        add_plugin_hooks(lint_data_tree)
        return lint_data_tree

    def test_a_tree_with_both_manifests_and_both_hooks_is_clean(self, plugin_tree: Path) -> None:
        assert audit(plugin_tree) == []

    @pytest.mark.parametrize("hook", ["check-jsonschema", "claude-plugin-validate"])
    def test_each_hook_missing(self, plugin_tree: Path, hook: str) -> None:
        edit(plugin_tree, f"      - id: {hook}\n", "      - id: project-check\n")
        findings = audit(plugin_tree)
        assert pairs(findings) == {(hook, "missing-hook")}
        assert findings[0].topic == "agent-plugins"

    def test_each_hook_stray(self, lint_data_tree: Path) -> None:
        add_plugin_hooks(lint_data_tree)
        assert pairs(audit(lint_data_tree)) == {
            ("check-jsonschema", "stray-hook"),
            ("claude-plugin-validate", "stray-hook"),
        }

    def test_one_manifest_kind_derives_its_check_alone(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, {".claude-plugin/marketplace.json": "{}"})
        add_plugin_hooks(lint_data_tree)
        assert pairs(audit(lint_data_tree)) == {("check-jsonschema", "stray-hook")}

    def test_the_validator_without_strict(self, plugin_tree: Path) -> None:
        edit(plugin_tree, "validate --strict", "validate")
        findings = audit(plugin_tree)
        assert pairs(findings) == {("claude-plugin-validate", "hook-args")}
        assert "--strict" in findings[0].detail

    def test_the_validator_looping_under_set_e(self, plugin_tree: Path) -> None:
        edit(
            plugin_tree,
            '\'for f in "$@"; do claude plugin validate --strict "$f" || exit 1; done\'',
            '\'set -e; for f in "$@"; do claude plugin validate --strict "$f"; done\'',
        )
        assert audit(plugin_tree) == []

    def test_the_schema_check_at_commit(self, plugin_tree: Path) -> None:
        edit(plugin_tree, SCHEMA_STAGE, SCHEMA_STAGE.removesuffix(MANUAL_STAGE))
        findings = audit(plugin_tree)
        assert pairs(findings) == {("check-jsonschema", "hook-args")}
        assert "manual" in findings[0].detail

    def test_the_schema_check_owes_no_always_run(self, plugin_tree: Path) -> None:
        assert "always_run" not in (plugin_tree / CONFIG).read_text().split("check-jsonschema")[1]
        assert audit(plugin_tree) == []

    def test_the_schema_flag_joined_by_an_equals_sign(self, plugin_tree: Path) -> None:
        edit(plugin_tree, f"--schemafile, {SCHEMA_URL}", f"--schemafile={SCHEMA_URL}")
        assert audit(plugin_tree) == []

    def test_another_agent_plugins_schema_version(self, plugin_tree: Path) -> None:
        edit(plugin_tree, "schemas/1.0.0/", "schemas/2.0.0/", CONFIG)
        assert audit(plugin_tree) == []

    def test_a_schema_check_of_another_schema_does_not_satisfy_the_set(
        self, plugin_tree: Path
    ) -> None:
        edit(plugin_tree, SCHEMA_URL, "https://json.schemastore.org/package.json", CONFIG)
        edit(plugin_tree, SCHEMA_STAGE, SCHEMA_STAGE.removesuffix(MANUAL_STAGE))
        assert pairs(audit(plugin_tree)) == {("check-jsonschema", "missing-hook")}

    def test_a_schema_check_of_another_schema_is_the_project_s(self, lint_data_tree: Path) -> None:
        with (lint_data_tree / CONFIG).open("a") as stream:
            stream.write(
                "\n  - repo: https://github.com/python-jsonschema/check-jsonschema\n"
                "    rev: 0.39.0\n    hooks:\n      - id: check-jsonschema\n"
                "        args: [--schemafile, schemas/settings.json]\n"
                "        files: ^settings/\n"
            )
        assert audit(lint_data_tree) == []

    def test_the_audit_still_owes_always_run(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "        always_run: true\n", "")
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("pip-audit", "hook-args")}
        assert "always_run" in findings[0].detail


WORKFLOW = {".github/workflows/ci.yml": "on: push\njobs: {}\n"}

CI_HOOKS = """
  - repo: https://github.com/rhysd/actionlint
    rev: v1.7.12
    hooks:
      - id: actionlint

  - repo: https://github.com/zizmorcore/zizmor-pre-commit
    rev: v1.24.1
    hooks:
      - id: zizmor
        args: [--offline, --no-progress]

  - repo: https://github.com/python-jsonschema/check-jsonschema
    rev: 0.39.0
    hooks:
      - id: check-github-workflows
"""

CI_IDS = ("actionlint", "zizmor", "check-github-workflows")


def add_ci_hooks(tree: Path) -> None:
    with (tree / CONFIG).open("a") as stream:
        stream.write(CI_HOOKS)


class TestCi:
    def test_a_workflow_with_none_of_the_trio(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, WORKFLOW)
        findings = audit(lint_data_tree)
        assert pairs(findings) == {(hook, "missing-hook") for hook in CI_IDS}
        assert {finding.topic for finding in findings} == {"ci"}

    def test_a_workflow_with_the_trio_is_clean(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, WORKFLOW)
        add_ci_hooks(lint_data_tree)
        assert audit(lint_data_tree) == []

    @pytest.mark.parametrize(
        ("kept", "dropped"), [("--no-progress", "--offline"), ("--offline", "--no-progress")]
    )
    def test_the_auditor_without_a_flag(
        self, lint_data_tree: Path, kept: str, dropped: str
    ) -> None:
        track(lint_data_tree, WORKFLOW)
        add_ci_hooks(lint_data_tree)
        edit(
            lint_data_tree,
            "zizmor\n        args: [--offline, --no-progress]",
            f"zizmor\n        args: [{kept}]",
        )
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("zizmor", "hook-args")}
        assert dropped in findings[0].detail

    def test_the_trio_without_a_workflow_is_stray(self, lint_data_tree: Path) -> None:
        add_ci_hooks(lint_data_tree)
        assert pairs(audit(lint_data_tree)) == {(hook, "stray-hook") for hook in CI_IDS}

    def test_an_action_or_dependabot_file_derives_none(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, {"action.yml": "name: a\n", ".github/dependabot.yml": "version: 2\n"})
        assert audit(lint_data_tree) == []


class TestForm:
    def test_a_locked_tree_s_by_name_entry(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "entry: uv run mypy", "entry: mypy")
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("mypy", "hook-form")}
        assert "skills/lint/references/python.md" in findings[0].detail

    def test_a_locked_tree_s_by_name_justfile_loop(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "uv run just --fmt", "just --fmt")
        assert pairs(audit(lint_data_tree)) == {("format-justfile", "hook-form")}

    def test_flags_between_the_runner_and_the_tool(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "entry: uv run mypy", "entry: uv run --frozen --group lint mypy")
        assert audit(lint_data_tree) == []

    def test_a_lockless_tree_s_runner_entry(self, lint_data_tree_builder: Tree) -> None:
        assert ("mypy", "hook-form") in pairs(audit(lint_data_tree_builder("lockless")))

    def test_a_lockless_tree_s_by_name_entries_are_fine(self, lint_data_tree_builder: Tree) -> None:
        found = pairs(audit(lint_data_tree_builder("lockless")))
        assert ("ty", "hook-form") not in found
        assert ("format-justfile", "hook-form") not in found

    def test_a_wrapper_gets_no_verdict(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "entry: uv run mypy", "entry: just typecheck")
        assert audit(lint_data_tree) == []

    def test_a_web_hook_s_executor_follows_the_lockfile(self, web_tree: Path) -> None:
        edit(web_tree, "pnpm run typecheck", "npm run typecheck")
        findings = audit(web_tree)
        assert pairs(findings) == {("typecheck", "hook-form")}
        assert "pnpm" in findings[0].detail


# The scanners as a collection of roles that pins nothing carries them, after
# its convergence: hosted at their own `rev:`, the second by name.
HOSTED_SCANNERS = """\
  - repo: https://github.com/ansible/ansible-lint
    rev: v26.11.0
    hooks:
      - id: ansible-lint
        args: [--offline]
        additional_dependencies: [ansible]
        files: ^(roles|meta)/|^galaxy\\.yml$
        exclude: \\.sops\\.ya?ml$
        always_run: false
        require_serial: true
        pass_filenames: false

  - repo: https://github.com/bridgecrewio/checkov
    rev: 3.4.3
    hooks:
      - id: checkov
        entry: checkov --quiet --directory roles
        files: ^roles/
        pass_filenames: false

"""

LOCAL_TRIVY = """\
      - id: trivy-config
        name: trivy config
        entry: trivy config --exit-code 1 --severity HIGH,CRITICAL roles
        language: system
        files: ^roles/
        pass_filenames: false
"""

BASELINE_AND_MARKUP = """\
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: mixed-line-ending
        args: [--fix=lf]
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: check-symlinks
      - id: destroyed-symlinks
      - id: check-executables-have-shebangs
      - id: check-shebang-scripts-are-executable
      - id: debug-statements
      - id: detect-private-key

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks

  - repo: https://github.com/crate-ci/typos
    rev: v1.51.1
    hooks:
      - id: typos

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.38.0
    hooks:
      - id: yamllint
        args: [--strict]

  - repo: https://github.com/ComPWA/taplo-pre-commit
    rev: v0.9.3
    hooks:
      - id: taplo-format

  - repo: https://github.com/rvben/rumdl-pre-commit
    rev: v0.3.0
    hooks:
      - id: rumdl-check
        args: [--fix]

  - repo: https://github.com/lycheeverse/lychee
    rev: lychee-v0.24.2
    hooks:
      - id: lychee
        args: [LYCHEE_VERSION=0.24.2, --offline, --no-progress]
        types: [markdown]

  - repo: local
    hooks:
      - id: format-justfile
        name: format justfile
        entry: bash -c 'for f in "$@"; do just --fmt --unstable --justfile "$f"; done' --
        language: system
        files: (^|/)justfile$|\\.just$

      - id: nixfmt
        name: nixfmt
        entry: nixfmt
        language: system
        files: \\.nix$

"""

ANSIBLE_YAMLLINT = """\
  comments:
    min-spaces-from-content: 1
  comments-indentation: false
  braces:
    min-spaces-inside: 0
    max-spaces-inside: 1
  octal-values:
    forbid-implicit-octal: true
    forbid-explicit-octal: true
"""

ROLES_CONTENT = {
    "galaxy.yml": "namespace: house\nname: roles\n",
    "meta/runtime.yml": "requires_ansible: '>=2.19'\n",
    "roles/web/tasks/main.yml": "- name: Ping\n  ansible.builtin.ping:\n",
}

LOCAL_CHECKOV = """\
      - id: checkov
        name: checkov
        entry: {entry}
        language: system
        files: ^roles/
        pass_filenames: false
"""


def _drop_hosted(tree: Path, repository: str) -> None:
    """Remove one hosted repository's block from the configuration."""
    text = (tree / CONFIG).read_text()
    blocks = text.split("\n\n")
    marker = f"repo: https://github.com/{repository}\n"
    kept = [block for block in blocks if marker not in block]
    assert len(kept) == len(blocks) - 1, repository
    (tree / CONFIG).write_text("\n\n".join(kept))


class TestHostedForm:
    @pytest.fixture
    def roles_tree(self, lint_tree_builder: Callable[..., Path]) -> Path:
        """A collection of roles that pins nothing, its scanners hosted."""
        yamllint = "extends: default\n\nrules:\n  document-start: disable\n  line-length:\n"
        rumdl = (
            "[MD013]\nline_length = 120\ntables = false\ncode_blocks = false\n\n"
            "[MD041]\nenabled = false\n"
        )
        return lint_tree_builder(
            {
                CONFIG: BASELINE_AND_MARKUP + LOCAL_TRIVY + "\n" + HOSTED_SCANNERS,
                ".yamllint.yaml": yamllint + "    max: 120\n" + ANSIBLE_YAMLLINT,
                ".rumdl.toml": rumdl,
                "README.md": "# Roles\n",
                **ROLES_CONTENT,
            }
        )

    def test_a_lockless_collection_with_hosted_scanners_is_clean(self, roles_tree: Path) -> None:
        assert audit(roles_tree) == []

    @pytest.mark.parametrize(
        "entry", ["checkov --quiet --directory roles", "uv run checkov --quiet --directory roles"]
    )
    def test_a_lockless_local_scanner_owes_the_hosted_form(
        self, roles_tree: Path, entry: str
    ) -> None:
        _drop_hosted(roles_tree, "bridgecrewio/checkov")
        add_local_hooks(roles_tree, LOCAL_CHECKOV.format(entry=entry))
        findings = audit(roles_tree)
        assert pairs(findings) == {("checkov", "hook-form")}
        assert "https://github.com/bridgecrewio/checkov" in findings[0].detail
        assert "`rev:`" in findings[0].detail
        assert "skills/lint/references/scanning.md" in findings[0].detail

    def test_a_lockless_local_ansible_linter_owes_the_hosted_form(self, roles_tree: Path) -> None:
        _drop_hosted(roles_tree, "ansible/ansible-lint")
        add_local_hooks(roles_tree, ANSIBLE_HOOKS.split("      - id: checkov")[0])
        findings = audit(roles_tree)
        assert pairs(findings) == {("ansible-lint", "hook-form")}
        assert "https://github.com/ansible/ansible-lint" in findings[0].detail

    def test_a_lockless_wrapper_gets_no_verdict(self, roles_tree: Path) -> None:
        _drop_hosted(roles_tree, "bridgecrewio/checkov")
        add_local_hooks(roles_tree, LOCAL_CHECKOV.format(entry="just scan"))
        assert audit(roles_tree) == []

    def test_a_mirror_is_not_judged(self, roles_tree: Path) -> None:
        edit(roles_tree, "github.com/bridgecrewio/checkov", "github.com/someone/checkov-mirror")
        assert audit(roles_tree) == []

    def test_a_locked_tree_s_hosted_scanners_owe_the_runner(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, ROLES_CONTENT)
        with (lint_data_tree / ".yamllint.yaml").open("a") as stream:
            stream.write(ANSIBLE_YAMLLINT)
        edit(lint_data_tree, "  - repo: local\n", f"{HOSTED_SCANNERS}  - repo: local\n")
        add_local_hooks(lint_data_tree, LOCAL_TRIVY)
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("ansible-lint", "hook-form"), ("checkov", "hook-form")}
        topics = {"ansible-lint": "ansible", "checkov": "scanning"}
        for finding in findings:
            assert "`uv run`" in finding.detail
            assert f"skills/lint/references/{topics[finding.subject]}.md" in finding.detail

    @pytest.mark.parametrize("dependencies", ["[ansible-core]", "[]"])
    def test_a_hosted_ansible_linter_without_the_collections(
        self, roles_tree: Path, dependencies: str
    ) -> None:
        edit(roles_tree, "dependencies: [ansible]", f"dependencies: {dependencies}")
        findings = audit(roles_tree)
        assert pairs(findings) == {("ansible-lint", "hook-args")}
        assert "`ansible`" in findings[0].detail
        assert findings[0].topic == "ansible"

    def test_a_pinned_collections_dependency_will_do(self, roles_tree: Path) -> None:
        edit(roles_tree, "dependencies: [ansible]", "dependencies: ['ansible>=11']")
        assert audit(roles_tree) == []


class TestOrder:
    CHECKS = """\
  - repo: https://github.com/dbt-checkpoint/dbt-checkpoint
    rev: v2.0.7
    hooks:
      - id: check-model-has-description
      - id: check-model-has-tests

"""
    PARSE = """\
      - id: sqlfluff-fix
        entry: uv run sqlfluff fix
        language: system
        types: [sql]
      - id: dbt-parse
        entry: uv run dbt parse --project-dir dbt
        language: system
        types_or: [yaml, sql]
        pass_filenames: false
"""

    def test_a_manifest_check_before_the_parse(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, {"dbt/dbt_project.yml": ""})
        add_local_hooks(lint_data_tree, self.PARSE)
        edit(lint_data_tree, "  - repo: local\n", f"{self.CHECKS}  - repo: local\n")
        assert pairs(audit(lint_data_tree)) == {
            ("check-model-has-description", "hook-order"),
            ("check-model-has-tests", "hook-order"),
        }

    def test_the_parse_first(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, {"dbt/dbt_project.yml": ""})
        add_local_hooks(lint_data_tree, self.PARSE)
        with (lint_data_tree / CONFIG).open("a") as stream:
            stream.write("\n" + self.CHECKS)
        assert audit(lint_data_tree) == []


class TestPins:
    def test_a_commit_hash(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "rev: v6.0.0", "rev: 2c9f875913ee60ca25ce70243dc24d5b6415598c")
        rule = {f.rule for f in audit(lint_data_tree)}
        assert rule == {RuleId.REV_PIN}

    def test_the_spelling_checker_on_its_moving_tag(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "rev: v1.50.3", "rev: v1")
        assert {f.rule for f in audit(lint_data_tree)} == {RuleId.REV_PIN}

    def test_a_short_tag_on_another_repository_is_fine(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "rev: v6.0.0", "rev: v1")
        assert audit(lint_data_tree) == []

    def test_an_old_tag_is_the_procedure_s(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "rev: v6.0.0", "rev: v0.0.1")
        assert audit(lint_data_tree) == []


class TestLinterFiles:
    def test_the_yaml_linter_s_file_is_absent(self, lint_data_tree: Path) -> None:
        (lint_data_tree / ".yamllint.yaml").unlink()
        assert pairs(audit(lint_data_tree)) == {("", "missing-config")}

    def test_either_name_of_it_will_do(self, lint_data_tree: Path) -> None:
        (lint_data_tree / ".yamllint.yaml").rename(lint_data_tree / ".yamllint")
        assert audit(lint_data_tree) == []

    def test_the_markdown_linter_s_file_is_absent(self, lint_data_tree: Path) -> None:
        (lint_data_tree / ".rumdl.toml").unlink()
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("", "missing-config")}
        assert findings[0].source == lint_data_tree / ".rumdl.toml"

    def test_a_lockfile_owes_the_spelling_checker_a_file(self, lint_data_tree: Path) -> None:
        (lint_data_tree / "_typos.toml").unlink()
        finding = audit(lint_data_tree)[0]
        assert finding.rule is RuleId.MISSING_CONFIG
        assert finding.topic == "baseline"

    def test_a_node_lockfile_with_no_web_source_owes_it_too(
        self, lint_data_tree_builder: Tree
    ) -> None:
        tree = lint_data_tree_builder("umbrella")
        track(tree, {"package.json": "{}", "package-lock.json": ""})
        assert {f.source.name for f in audit(tree)} == {"_typos.toml"}

    def test_a_submodule_owes_it_too(self, lint_data_tree_builder: Tree) -> None:
        tree = lint_data_tree_builder("umbrella")
        assert audit(tree) == []
        track(tree, {".gitmodules": ""})
        assert {f.source.name for f in audit(tree)} == {"_typos.toml"}

    def test_a_wrong_width(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "line_length = 120", "line_length = 100", ".rumdl.toml")
        findings = audit(lint_data_tree)
        assert pairs(findings) == {("MD013.line_length", "config-value")}
        assert findings[0].source == lint_data_tree / ".rumdl.toml"

    def test_a_wrong_yaml_value(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "max: 120", "max: 80", ".yamllint.yaml")
        assert pairs(audit(lint_data_tree)) == {("rules.line-length.max", "config-value")}

    def test_ansible_content_adds_six_values(self, lint_data_tree: Path) -> None:
        track(lint_data_tree, {"ansible/site.yml": ""})
        add_local_hooks(lint_data_tree, ANSIBLE_HOOKS)
        found = audit(lint_data_tree)
        assert {f.rule for f in found} == {RuleId.CONFIG_VALUE}
        assert len(found) == 6

    def test_a_repository_wide_disable(self, lint_data_tree: Path) -> None:
        (lint_data_tree / ".shellcheckrc").write_text("external-sources=true\ndisable=SC2034\n")
        assert pairs(audit(lint_data_tree)) == {("disable", "shellcheck-disable")}

    def test_a_shell_checker_file_with_no_disable(self, lint_data_tree: Path) -> None:
        (lint_data_tree / ".shellcheckrc").write_text("external-sources=true\n")
        assert audit(lint_data_tree) == []

    def test_a_linter_file_that_does_not_parse(self, lint_data_tree: Path) -> None:
        (lint_data_tree / ".rumdl.toml").write_text("[MD013\n")
        assert pairs(audit(lint_data_tree)) == {("", "parse")}


class TestPythonProjectValues:
    PROJECT = "pyproject.toml"
    SELECT = "tool.ruff.lint.select"

    def test_the_security_rules_are_absent(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, 'extend-select = ["S"]', 'select = ["E"]', self.PROJECT)
        finding = audit(lint_data_tree)
        assert pairs(finding) == {(self.SELECT, "config-value")}
        assert finding[0].source == lint_data_tree / self.PROJECT

    @pytest.mark.parametrize("key", ["select", "extend-select"])
    def test_the_security_rules_are_enabled_either_way(
        self, lint_data_tree: Path, key: str
    ) -> None:
        edit(lint_data_tree, 'extend-select = ["S"]', f'{key} = ["E", "S"]', self.PROJECT)
        assert audit(lint_data_tree) == []

    def test_a_house_ignore_is_absent(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, 'ignore = ["S603", "S607"]', 'ignore = ["S603"]', self.PROJECT)
        finding = audit(lint_data_tree)
        assert pairs(finding) == {("tool.ruff.lint.ignore", "config-value")}
        assert "S607" in finding[0].detail

    def test_a_test_ignore_is_absent(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, '"S101", "S105", "S106", "S107"', '"S101"', self.PROJECT)
        finding = audit(lint_data_tree)
        assert [f.rule for f in finding] == [RuleId.CONFIG_VALUE]
        assert "S105, S106, S107" in finding[0].detail

    @pytest.mark.parametrize("glob", ["tests/**/*.py", "**/tests/**"])
    def test_a_spelling_of_the_test_tree_is_the_test_tree(
        self, lint_data_tree: Path, glob: str
    ) -> None:
        edit(lint_data_tree, '"tests/**" = ', f'"{glob}" = ', self.PROJECT)
        assert audit(lint_data_tree) == []

    def test_the_extending_table_is_read_too(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, ".per-file-ignores]", ".extend-per-file-ignores]", self.PROJECT)
        assert audit(lint_data_tree) == []

    def test_a_repository_with_no_test_tree_owes_no_test_ignores(
        self, lint_data_tree: Path
    ) -> None:
        edit(lint_data_tree, '"tests/**" = ["S101", "S105", "S106", "S107"]', "", self.PROJECT)
        (lint_data_tree / "tests" / "test_app.py").unlink()
        track(lint_data_tree, {})
        assert audit(lint_data_tree) == []

    def test_the_cooldown_is_absent(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, 'exclude-newer = "7 days"', 'exclude-newer = "1 day"', self.PROJECT)
        assert pairs(audit(lint_data_tree)) == {("tool.uv.exclude-newer", "config-value")}

    def test_the_runner_form_owes_the_dev_group(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, '"ty>=0.0.1", "rust-just>=1.40"', '"ty>=0.0.1"', self.PROJECT)
        assert pairs(audit(lint_data_tree)) == {("dependency-groups.dev.rust-just", "config-value")}

    def test_a_lockless_project_owes_neither(self, lint_data_tree_builder: Tree) -> None:
        found = pairs(audit(lint_data_tree_builder("lockless")))
        assert ("tool.uv.exclude-newer", "config-value") not in found
        assert ("dependency-groups.dev.ty", "config-value") not in found

    def test_ruff_s_own_file_is_read_first(self, lint_data_tree: Path) -> None:
        (lint_data_tree / "ruff.toml").write_text('[lint]\nselect = ["E"]\n')
        assert {f.source.name for f in audit(lint_data_tree)} == {"ruff.toml"}

    def test_a_project_file_that_does_not_parse(self, lint_data_tree: Path) -> None:
        (lint_data_tree / self.PROJECT).write_text("[project\n")
        assert pairs(audit(lint_data_tree)) == {("", "parse")}


class TestExcludedSignals:
    def test_a_vendored_dockerfile_every_hook_excludes_derives_no_hook(
        self, lint_data_tree: Path
    ) -> None:
        track(lint_data_tree, {"vendor/mcp/Dockerfile": ""})
        assert pairs(audit(lint_data_tree)) == {("hadolint", "missing-hook")}
        edit(lint_data_tree, "repos:\n", "exclude: ^vendor/\n\nrepos:\n")
        assert audit(lint_data_tree) == []


class TestWhatBelongsToTheProject:
    def test_a_project_s_own_hook(self, lint_data_tree: Path) -> None:
        assert "generated-drift" in (lint_data_tree / CONFIG).read_text()
        assert audit(lint_data_tree) == []

    def test_a_two_directory_terraform_loop(self, terraform_tree: Path) -> None:
        assert audit(terraform_tree) == []

    def test_one_directory_the_project_chose(self, terraform_tree: Path) -> None:
        edit(terraform_tree, "--chdir infra", "--chdir deploy/layers")
        assert audit(terraform_tree) == []

    def test_an_entry_exclude(self, lint_data_tree: Path) -> None:
        edit(
            lint_data_tree,
            "      - id: yamllint\n",
            "      - id: yamllint\n        exclude: ^generated/\n",
        )
        assert audit(lint_data_tree) == []

    def test_a_top_level_exclude(self, lint_data_tree: Path) -> None:
        edit(lint_data_tree, "repos:\n", "exclude: ^vendor/\nfail_fast: true\n\nrepos:\n")
        assert audit(lint_data_tree) == []

    def test_the_order_of_the_hooks(self, lint_data_tree: Path) -> None:
        text = (lint_data_tree / CONFIG).read_text()
        head, *blocks = text.split("  - repo: ")
        (lint_data_tree / CONFIG).write_text("  - repo: ".join([head, *reversed(blocks)]))
        assert audit(lint_data_tree) == []

    def test_an_allowlist_s_contents(self, lint_data_tree: Path) -> None:
        (lint_data_tree / ".gitleaks.toml").write_text('[allowlist]\npaths = ["tests/"]\n')
        (lint_data_tree / ".trivyignore").write_text("AVD-AWS-0001\n")
        assert audit(lint_data_tree) == []


class TestGoverned:
    @pytest.mark.parametrize(
        "name",
        [
            ".pre-commit-config.yaml",
            ".yamllint",
            "_typos.toml",
            ".eslintrc.json",
            "eslint.config.js",
        ],
    )
    def test_a_name_the_topics_attach_on(self, name: str) -> None:
        assert is_governed(Path("/anywhere") / name)

    @pytest.mark.parametrize("name", ["pyproject.toml", "README.md", "justfile"])
    def test_a_name_they_do_not(self, name: str) -> None:
        assert not is_governed(Path("/anywhere") / name)

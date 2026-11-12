"""The `compliant` tree with one more language tracked and its hooks added,
and the two edits a test makes to a tree's hook configuration.
"""

from pathlib import Path

import pytest

from tests.fixtures.lintlint.trees import track

CONFIG = ".pre-commit-config.yaml"


def edit(tree: Path, old: str, new: str, file: str = CONFIG) -> None:
    path = tree / file
    text = path.read_text()
    assert old in text, f"{old!r} is not in {file}"
    path.write_text(text.replace(old, new))


def add_local_hooks(tree: Path, text: str) -> None:
    edit(tree, "  - repo: local\n    hooks:\n", f"  - repo: local\n    hooks:\n{text}")


TERRAFORM_HOOKS = """\
      - id: terraform-fmt
        entry: terraform fmt -recursive infra
        language: system
        files: ^infra/
        pass_filenames: false
      - id: terraform-validate
        entry: >-
          bash -c 'rc=0; for d in "$@"; do terraform -chdir="$d" validate || rc=1; done; exit $rc'
          -- infra infra/bootstrap
        language: system
        files: ^infra/
        pass_filenames: false
      - id: tflint
        entry: tflint --chdir infra --recursive
        language: system
        files: ^infra/
        pass_filenames: false
      - id: checkov
        entry: uv run checkov --quiet --directory infra
        language: system
        files: ^infra/
        pass_filenames: false
      - id: trivy-config
        entry: trivy config --exit-code 1 --severity HIGH,CRITICAL infra
        language: system
        files: ^infra/
        pass_filenames: false
"""

WEB_HOOKS = """\
      - id: eslint
        entry: pnpm exec eslint --fix
        language: system
        types_or: [ts, tsx, javascript, jsx]
        require_serial: true
      - id: prettier
        entry: pnpm exec prettier --write --ignore-unknown
        language: system
        types_or: [ts, tsx, javascript, jsx, css, html]
        require_serial: true
      - id: typecheck
        entry: pnpm run typecheck
        language: system
        types_or: [ts, tsx]
        pass_filenames: false
        require_serial: true
"""


@pytest.fixture
def terraform_tree(lint_data_tree: Path) -> Path:
    track(lint_data_tree, {"infra/main.tf": ""})
    add_local_hooks(lint_data_tree, TERRAFORM_HOOKS)
    return lint_data_tree


@pytest.fixture
def web_tree(lint_data_tree: Path) -> Path:
    track(
        lint_data_tree,
        {"package.json": "{}", "pnpm-lock.yaml": "", "_typos.toml": "", "web/src/main.ts": ""},
    )
    add_local_hooks(lint_data_tree, WEB_HOOKS)
    return lint_data_tree

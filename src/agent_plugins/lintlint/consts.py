"""Module constants: the rule table, the house set, and the hook's limits."""

import re
from datetime import timedelta
from pathlib import PurePosixPath

from agent_plugins.lintlint.types import (
    Canon,
    FormTool,
    HostedTool,
    HouseHook,
    Replacement,
    Rule,
    RuleId,
    Signal,
)

# Every rule id names the `lint-rules` topic file that states it; a rule that
# spans topics carries the specific one on the finding. The fix is one line and
# holds no rationale: the cited topic carries that, and a finding that restated
# it would be a second copy to drift.
RULES: dict[RuleId, Rule] = {
    RuleId.PARSE: Rule("make the file parse, with a list of `repos:` in a hook file", "applying"),
    RuleId.NO_CONFIGURATION: Rule("write the set this repository derives", "applying"),
    RuleId.MISSING_HOOK: Rule("add the house entry", "applying"),
    RuleId.STRAY_HOOK: Rule("remove the hook: its set's signal is gone", "applying"),
    RuleId.RETIRED_TOOL: Rule("replace it with the house tool", "applying"),
    RuleId.HOOK_ARGS: Rule("restore the canonical entry", "stages"),
    RuleId.HOOK_FORM: Rule("take the form the lockfile signal rules in", "applying"),
    RuleId.HOOK_ORDER: Rule("list `dbt-parse` before the checks reading its manifest", "data"),
    RuleId.REV_PIN: Rule("pin the newest release tag past the cooldown", "versions"),
    RuleId.MISSING_CONFIG: Rule("write the file with the house values", "markup"),
    RuleId.CONFIG_VALUE: Rule("set the house value", "markup"),
    RuleId.SHELLCHECK_DISABLE: Rule("suppress at the line, naming code and reason", "shell"),
}

# How a rule file is cited: `skills/lint/references/<topic>.md`, relative to the plugin.
TOPIC_TEMPLATE = "skills/lint/references/{topic}.md"

HOOK_CONFIG_NAME = ".pre-commit-config.yaml"

# Every id the topics carry, each under the signal that derives it. The fifteen
# hygiene ids are taken whole, so each is its own line.
HOUSE_HOOKS: tuple[HouseHook, ...] = (
    *(
        HouseHook(hook_id, "baseline", Signal.ALWAYS)
        for hook_id in (
            "trailing-whitespace",
            "end-of-file-fixer",
            "mixed-line-ending",
            "check-yaml",
            "check-toml",
            "check-json",
            "check-added-large-files",
            "check-merge-conflict",
            "check-case-conflict",
            "check-symlinks",
            "destroyed-symlinks",
            "check-executables-have-shebangs",
            "check-shebang-scripts-are-executable",
            "debug-statements",
            "detect-private-key",
            "gitleaks",
            "typos",
            "format-justfile",
            "nixfmt",
        )
    ),
    *(
        HouseHook(hook_id, "python", Signal.PYTHON)
        for hook_id in ("ruff-check", "ruff-format", "validate-pyproject", "mypy", "ty")
    ),
    HouseHook("uv-lock", "python", Signal.PYTHON_LOCK),
    HouseHook("pip-audit", "python", Signal.PYTHON_LOCK),
    HouseHook("yamllint", "markup", Signal.MARKUP),
    HouseHook("taplo-format", "markup", Signal.MARKUP),
    HouseHook("rumdl-check", "markup", Signal.MARKUP),
    HouseHook("lychee", "markup", Signal.MARKUP),
    HouseHook("shellcheck", "shell", Signal.SHELL),
    HouseHook("terraform-fmt", "terraform", Signal.TERRAFORM),
    HouseHook("terraform-validate", "terraform", Signal.TERRAFORM),
    HouseHook("tflint", "terraform", Signal.TERRAFORM),
    HouseHook("ansible-lint", "ansible", Signal.ANSIBLE),
    HouseHook("hadolint", "dockerfile", Signal.DOCKERFILE),
    HouseHook("checkov", "scanning", Signal.SCANNED),
    HouseHook("trivy-config", "scanning", Signal.SCANNED),
    HouseHook("eslint", "web", Signal.WEB),
    HouseHook("prettier", "web", Signal.WEB),
    HouseHook("typecheck", "web", Signal.WEB),
    HouseHook("sqlfluff-fix", "data", Signal.DATA),
    HouseHook("dbt-parse", "data", Signal.DATA),
    HouseHook("check-model-has-description", "data", Signal.DATA),
    HouseHook("check-model-has-tests", "data", Signal.DATA),
    HouseHook("check-jsonschema", "agent-plugins", Signal.PORTABLE_MANIFEST),
    HouseHook("claude-plugin-validate", "agent-plugins", Signal.CLAUDE_MANIFEST),
    *(
        HouseHook(hook_id, "ci", Signal.WORKFLOWS)
        for hook_id in ("actionlint", "zizmor", "check-github-workflows")
    ),
)

# Tools the standard retires, found by hook id or as a word of a local entry.
RETIRED_TOOLS: dict[str, Replacement] = {
    "codespell": Replacement("typos", "markup"),
    "pyright": Replacement("the mypy and ty pair", "python"),
    "bandit": Replacement("ruff's security rules", "python"),
    "dprint": Replacement("the markup tools", "markup"),
}

# Retired under one spelling only: the tool itself stays.
RETIRED_IDS: dict[str, Replacement] = {
    "ruff": Replacement("ruff-check", "python"),
    "hadolint-docker": Replacement("hadolint", "dockerfile"),
}

# Retired as hook repositories, matched on the path of the URL.
RETIRED_REPOS: dict[str, Replacement] = {
    "instrumentl/pre-commit-just": Replacement("format-justfile", "baseline"),
    "pre-commit/mirrors-mypy": Replacement("the local mypy hook", "python"),
    "pypa/pip-audit": Replacement("the local pip-audit hook", "python"),
}

# A pin of the formatter buried in a hook entry.
RETIRED_ENTRY_PIN = "rust-just=="
RETIRED_ENTRY_PIN_REPLACEMENT = Replacement("the lockfile's pin of the formatter", "baseline")

# The types a code formatter must leave to the house tools.
MARKUP_TYPES = frozenset({"markdown", "yaml", "json"})

# The canonical entries, hook by hook. What a hook here does not name, such as
# a directory argument or an exclusion, is the project's and never compared.
HOOK_CANON: dict[str, Canon] = {
    "mixed-line-ending": Canon("baseline", flags=("--fix=lf",)),
    "yamllint": Canon("markup", flags=("--strict",)),
    "rumdl-check": Canon("markup", flags=("--fix",)),
    # Supplying `args:` replaces upstream's `--no-progress`, so both are canon.
    "lychee": Canon("markup", flags=("--offline", "--no-progress")),
    "ansible-lint": Canon("ansible", flags=("--offline",), whole_program=True, serial=True),
    "pip-audit": Canon(
        "python",
        flags=("--no-emit-workspace",),
        whole_program=True,
        manual=True,
        always_run=True,
    ),
    "mypy": Canon("python", whole_program=True, filtered=True),
    "ty": Canon("python", whole_program=True, filtered=True),
    "typecheck": Canon("web", whole_program=True, filtered=True),
    "terraform-fmt": Canon("terraform", whole_program=True, filtered=True),
    "terraform-validate": Canon("terraform", whole_program=True, filtered=True),
    "tflint": Canon("terraform", whole_program=True, filtered=True),
    "checkov": Canon("scanning", whole_program=True, filtered=True),
    "trivy-config": Canon(
        "scanning",
        flags=("--exit-code 1", "--severity HIGH,CRITICAL"),
        whole_program=True,
        filtered=True,
    ),
    "dbt-parse": Canon("data", whole_program=True, filtered=True),
    "eslint": Canon("web", serial=True),
    "prettier": Canon("web", serial=True),
    # Handed the manifests it matches, so manual without `always_run`.
    "check-jsonschema": Canon("agent-plugins", manual=True),
    "claude-plugin-validate": Canon("agent-plugins", flags=("--strict",)),
    # Supplying `args:` replaces upstream's `--no-progress`, so both are canon.
    "zizmor": Canon("ci", flags=("--offline", "--no-progress")),
}

# The generic schema checker is the house hook only when pointed at the Agent
# Plugins schema, at whatever version the manifests declare; pointed at any
# other schema it is the project's.
SCHEMA_CHECK_ID = "check-jsonschema"
SCHEMA_FILE_FLAG = "--schemafile"
AGENT_PLUGINS_SCHEMA = re.compile(
    r"https://agent-plugins\.org/schemas/[^/\s]+/plugin\.schema\.json"
)

# The formatter's type list, the one hook whose filter is canonical to the item.
RUFF_FORMAT_TYPES = frozenset({"python", "pyi", "jupyter"})

# Supplying `args:` to the spelling checker replaces both of these.
TYPOS_DEFAULT_FLAGS = ("--write-changes", "--force-exclude")

# Local hooks the lockfile signal decides the form of: id, the tool they run,
# and the topic giving both forms.
FORM_TOOLS: dict[str, FormTool] = {
    "format-justfile": FormTool("just", "baseline"),
    "mypy": FormTool("mypy", "python"),
    "ty": FormTool("ty", "python"),
    "checkov": FormTool("checkov", "scanning"),
    "ansible-lint": FormTool("ansible-lint", "ansible"),
    "sqlfluff-fix": FormTool("sqlfluff", "data"),
    "dbt-parse": FormTool("dbt", "data"),
}

# Form tools a repository that tracks no lockfile hosts rather than calls by
# name: id, the upstream repository's path, and the topic giving the hosted
# entry. The standard's test is that pre-commit installs the tool and the hook's
# own dependencies carry all it needs; the checker cannot judge that, so the
# tools that meet it are listed. A hook hosted from any other repository, such
# as a mirror, gets no form verdict.
HOSTED_FORM_TOOLS: dict[str, HostedTool] = {
    "ansible-lint": HostedTool("ansible/ansible-lint", "ansible"),
    "checkov": HostedTool("bridgecrewio/checkov", "scanning"),
}
HOSTED_URL_TEMPLATE = "https://github.com/{repository}"

# What the hosted Ansible linter's own environment must carry to resolve, offline,
# the collection modules the content calls: the community package, not the core
# engine upstream installs.
ANSIBLE_LINT_ID = "ansible-lint"
ANSIBLE_COLLECTIONS_DEPENDENCY = "ansible"

# Which executor each node lockfile owes, and the ones a web hook may name.
NODE_LOCKFILES: dict[str, str] = {
    "pnpm-lock.yaml": "pnpm",
    "package-lock.json": "npm",
    "yarn.lock": "yarn",
}
WEB_EXECUTORS = ("pnpm", "npm", "npx", "yarn")
WEB_HOOKS = frozenset({"eslint", "prettier", "typecheck"})

# The hook repository whose checks read the manifest `dbt-parse` writes.
DBT_CHECKPOINT_REPO = "dbt-checkpoint/dbt-checkpoint"
DBT_PARSE_ID = "dbt-parse"

# The spelling checker's repository and its moving major tag.
TYPOS_REPO = "crate-ci/typos"
TYPOS_MOVING_TAG = "v1"

# The link checker's hosted script hook, its tag prefix, and the first argument
# that names its version. Without that argument the script finds its version
# with `git describe` inside its checkout, which a linked worktree's `GIT_DIR`
# redirects to the committing repository.
LYCHEE_REPO = "lycheeverse/lychee"
LYCHEE_ID = "lychee"
LYCHEE_TAG_PREFIX = "lychee-v"
LYCHEE_VERSION_ARG = "LYCHEE_VERSION="

# Hook repositories with no pin to compare.
PINLESS_REPOS = frozenset({"local", "meta"})

COMMIT_HASH = re.compile(r"[0-9a-f]{7,40}")
DISTRIBUTION_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

# Where a tool's name counts as the command: not inside a path, a flag or a
# longer name. The body of a `bash -c` loop is searched the same way.
WORD_START = r"(?<![\w/.=-])"
WORD_END = r"(?![\w.-])"

# The linter files, each under every name its tool reads; the first is the name
# a finding asks for.
YAMLLINT_FILES = (".yamllint.yaml", ".yamllint", ".yamllint.yml")
RUMDL_FILE = ".rumdl.toml"
TYPOS_FILES = ("_typos.toml", ".typos.toml")
SHELLCHECK_FILE = ".shellcheckrc"
SHELLCHECK_DISABLE = re.compile(r"^\s*disable\s*=", re.MULTILINE)
RUFF_FILES = (".ruff.toml", "ruff.toml")
PROJECT_FILE = "pyproject.toml"

YAMLLINT_VALUES: dict[str, object] = {
    "extends": "default",
    "rules.document-start": "disable",
    "rules.line-length.max": 120,
}

# The Ansible linter reads the YAML linter's file too and refuses other values.
YAMLLINT_ANSIBLE_VALUES: dict[str, object] = {
    "rules.comments.min-spaces-from-content": 1,
    "rules.comments-indentation": False,
    "rules.braces.min-spaces-inside": 0,
    "rules.braces.max-spaces-inside": 1,
    "rules.octal-values.forbid-implicit-octal": True,
    "rules.octal-values.forbid-explicit-octal": True,
}

# `false` and `disable` are one to the YAML linter.
YAMLLINT_DISABLED = ("disable", False)

RUMDL_VALUES: dict[str, object] = {
    "MD013.line_length": 120,
    "MD013.tables": False,
    "MD013.code_blocks": False,
    "MD041.enabled": False,
}

RUFF_SECTIONS = ("select", "extend-select")
RUFF_IGNORE_SECTIONS = ("ignore", "extend-ignore")
RUFF_SECURITY_RULES = "S"
RUFF_ALL_RULES = "ALL"
RUFF_IGNORES = frozenset({"S603", "S607"})
# The test tree, under the spellings a per-file table reaches it by: the house
# one and the ones narrower by file type or wider by depth, which say the same.
TESTS_DIR = "tests"
RUFF_TEST_GLOB = "tests/**"
RUFF_TEST_GLOBS = re.compile(r"(\*\*/)?tests/")
RUFF_PER_FILE_SECTIONS = ("per-file-ignores", "extend-per-file-ignores")
RUFF_TEST_IGNORES = frozenset({"S101", "S105", "S106", "S107"})

UV_COOLDOWN_KEY = "tool.uv.exclude-newer"
UV_COOLDOWN = "7 days"

# What the dev group carries where the Python set takes the runner form.
DEV_DEPENDENCIES = ("ty", "rust-just")

# Which signal each tracked name carries. The applying topic states the
# Kubernetes test — a YAML file with `apiVersion` and `kind` at its top level;
# this checker looks for both keys at the start of a line rather than parsing
# every tracked YAML file, because that would not fit the hook's budget.
PYTHON_PROJECT = "pyproject.toml"
PYTHON_SUFFIX = ".py"
LOCKFILE_NAME = "uv.lock"
SUBMODULES_FILE = ".gitmodules"
MARKUP_SUFFIXES = frozenset({".yaml", ".yml", ".toml", ".md"})
YAML_SUFFIXES = frozenset({".yaml", ".yml"})
SHELL_SUFFIX = ".sh"
SHELL_INTERPRETERS = ("sh", "bash", "dash", "ksh")
SHEBANG = re.compile(
    rb"^#!\s*(?:/usr/bin/env\s+(?:-S\s+)?)?(?:/\S*/)?(?:"
    + "|".join(SHELL_INTERPRETERS).encode()
    + rb")(?:\s|$)"
)
TERRAFORM_SUFFIX = ".tf"
ANSIBLE_DIR = "ansible"
ANSIBLE_MANIFEST = "galaxy.yml"
ROLES_DIR = "roles"
ROLE_TASKS_DIR = "tasks"
DOCKERFILE_NAME = "Dockerfile"
DOCKERFILE_SUFFIX = ".dockerfile"
HELM_MANIFEST = "Chart.yaml"
MANIFEST_READ_LIMIT = 256 * 1024
MANIFEST_KEYS = (re.compile(rb"^apiVersion:", re.M), re.compile(rb"^kind:", re.M))
WEB_MANIFEST = "package.json"
# The types the web set's linter and type check read; a manifest derives the
# set only with one of them under its directory.
WEB_SOURCE_SUFFIXES = frozenset({".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"})
DBT_PROJECT = "dbt_project.yml"
# The Claude manifests sit in the one directory their host reads; a portable
# manifest is a `plugin.json` anywhere else that declares the Agent Plugins
# schema. Other hosts' marketplace files carry no signal.
CLAUDE_PLUGIN_DIR = ".claude-plugin"
CLAUDE_MANIFESTS = frozenset({"plugin.json", "marketplace.json"})
PORTABLE_MANIFEST = "plugin.json"
SCHEMA_KEY = "$schema"
# The one directory the host reads workflows from, at the repository's root; an
# action's metadata file and the dependabot file carry no signal.
WORKFLOWS_DIR = PurePosixPath(".github/workflows")

# Git's mode for a nested repository's entry in the listing, and an executable.
GITLINK_MODE = "160000"
EXECUTABLE_MODE = "100755"

# The names the ratchet acts on: the union of every topic's `paths:`, without
# their `**/`. A test holds this equal to the topics and to `hooks.json`.
GOVERNED_GLOBS: tuple[str, ...] = (
    ".pre-commit-config.yaml",
    "_typos.toml",
    ".typos.toml",
    ".gitleaks.toml",
    "ruff.toml",
    ".ruff.toml",
    "mypy.ini",
    ".mypy.ini",
    "ty.toml",
    ".yamllint",
    ".yamllint.yaml",
    ".yamllint.yml",
    ".taplo.toml",
    "taplo.toml",
    ".rumdl.toml",
    ".shellcheckrc",
    ".tflint.hcl",
    ".checkov.yaml",
    ".checkov.yml",
    "trivy.yaml",
    ".trivyignore",
    ".ansible-lint",
    ".hadolint.yaml",
    "eslint.config.*",
    ".eslintrc*",
    ".prettierrc*",
    "prettier.config.*",
    ".sqlfluff",
    ".sqlfluffignore",
)

# What a file-level finding is named by when it has no subject.
FILE_SUBJECT = "<file>"

# How the hook's two reports lead, and what it says once when it cannot check.
POST_LEAD = "fix them now, before moving on"
STOP_LEAD = "still open; fix them before finishing"
NO_GIT_NOTICE = "lint-lint: `git` is not on PATH, so lint checks are off in this session."

# Marker names. The `git` notice is stated once per context; the Stop gate is
# keyed on the prompt, never on `stop_hook_active` — that flag is also true
# after another hook's block, which would skip this gate silently.
NO_GIT_MARKER = "no-git"
BLOCKED_MARKER = "blocked-{prompt}"

# `additionalContext` reaches the model inline up to 10,000 characters per
# hook; above it the harness hands over a preview the model need not open. A
# report that would exceed it is truncated with a count of the rest, so a large
# new file is still acted on.
INLINE_LIMIT = 10_000

# Where the ratchet keeps its per-context baselines. `CLAUDE_PLUGIN_DATA` is
# set for plugin hooks, and per plugin, so this cannot collide with `just-lint`;
# the fallback keeps `lint-lint hook` usable (and testable) outside a plugin.
STATE_ENV = "CLAUDE_PLUGIN_DATA"
STATE_DIR_NAME = "lint"
STATE_FALLBACK = ".cache/lint-lint"

# Prefix of the bookkeeping files, which are not baselines: markers and guards.
MARKER_PREFIX = "_"

# How much of a path's digest names its state file. Enough to separate the
# files of one context; the full path is stored inside the file.
DIGEST_LENGTH = 16

# State untouched for this long is pruned. Nothing is pruned at SessionEnd:
# desktop sessions are resumed after it, and a baseline dropped there would
# turn a violation left before the exit into legacy.
PRUNE_AFTER = timedelta(days=7)

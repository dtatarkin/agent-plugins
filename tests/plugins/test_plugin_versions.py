"""Holds each plugin's version to its files.

Claude Code caches an installed plugin by its version, so a change shipped
without a bump never reaches a user who already has that version. A release
is tagged `<name>--v<version>`. A plugin whose files differ from the tag of
the version its manifest declares was changed without a bump, and this fails
naming it. A version with no tag yet is a bump not yet released, and passes.

The comparison is against the working tree, which under pre-commit holds
exactly what is being committed. The `host-support` spec is the rule's home.
"""

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGINS = sorted(path.parent.name for path in REPO_ROOT.glob("plugins/*/plugin.json"))


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )


def _version(plugin: str) -> str:
    manifest = REPO_ROOT / "plugins" / plugin / "plugin.json"
    return json.loads(manifest.read_text())["version"]


def _tag(plugin: str) -> str:
    return f"{plugin}--v{_version(plugin)}"


def _tag_exists(tag: str) -> bool:
    return _git("rev-parse", "--quiet", "--verify", f"refs/tags/{tag}").returncode == 0


pytestmark = pytest.mark.skipif(
    not _git("tag", "--list", "*--v*").stdout.strip(),
    reason="this clone holds no plugin tags to compare against",
)


@pytest.mark.parametrize("plugin", PLUGINS, ids=str)
class TestAPluginAtATaggedVersion:
    def test_has_no_change_since_its_tag(self, plugin: str) -> None:
        tag = _tag(plugin)
        if not _tag_exists(tag):
            pytest.skip(f"{tag} is not tagged yet")
        changed = _git("diff", "--name-only", tag, "--", f"plugins/{plugin}").stdout.split()
        assert not changed, f"{plugin} changed since {tag} without a version bump: {changed}"

    def test_has_no_untracked_file(self, plugin: str) -> None:
        tag = _tag(plugin)
        if not _tag_exists(tag):
            pytest.skip(f"{tag} is not tagged yet")
        untracked = _git(
            "ls-files", "--others", "--exclude-standard", f"plugins/{plugin}"
        ).stdout.split()
        assert not untracked, (
            f"{plugin} has files added since {tag} without a version bump: {untracked}"
        )

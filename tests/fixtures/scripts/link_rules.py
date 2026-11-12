"""A throwaway repository holding a copy of `scripts/link-rules` and a small
tree of rule files for it to link.

`HOME` and `CLAUDE_CONFIG_DIR` point at throwaway directories, so the real
rules directory is never touched.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "link-rules"

SCOPED = "---\npaths:\n  - '**/*.alpha'\n---\n\n# A scoped topic\n"
NO_FRONTMATTER = "# An unscoped topic\n"
NO_PATHS = "---\ntitle: unscoped\n---\n\n# Frontmatter without paths\n"

# The tree the fixture builds: plugin -> topic -> content.
TREE = {
    "alpha-rules": {"one": SCOPED, "two": SCOPED, "plain": NO_FRONTMATTER},
    "beta-rules": {"three": SCOPED, "titled": NO_PATHS},
}


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
def link_setup(tmp_path: Path) -> Setup:
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

"""Holds the host-support record's table to the README's install blocks.

`docs/host-support.md` records what each supported host does with these
plugins, as one table with a column per host. The README is where a host
becomes supported: it gives the host an install block. Nothing else ties the
two, so a host added to the README without a column, a column left for a host
the README dropped, a row lost in an edit, or a cell left blank would go
unnoticed. This catches each, naming the host, row or cell.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
README = (REPO_ROOT / "README.md").read_text()
RECORD = (REPO_ROOT / "docs" / "host-support.md").read_text()
INSTALL_HEADING = re.compile(r"^## Install in (?:the )?(.+)$", re.MULTILINE)
REQUIRED_ROWS = (
    "Verified on",
    "Install sources run",
    "Skills",
    "Hooks",
    "Plugin manifest read",
    "Marketplace file read",
)
DELIMITER_CELL = re.compile(r"^:?-+:?$")


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _first_table(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            rows.append(_cells(line))
        elif rows:
            break
    if len(rows) > 1 and all(DELIMITER_CELL.match(cell) for cell in rows[1]):
        del rows[1]
    return rows


SUPPORTED_HOSTS = INSTALL_HEADING.findall(README)
TABLE = _first_table(RECORD)
HEADER = TABLE[0] if TABLE else []
BODY = {row[0]: row[1:] for row in TABLE[1:]}


def test_the_readme_names_supported_hosts() -> None:
    assert SUPPORTED_HOSTS


def test_the_record_holds_a_table() -> None:
    assert TABLE, "docs/host-support.md holds no table"


class TestTheColumns:
    def test_are_the_readme_hosts_in_order(self) -> None:
        assert HEADER[1:] == SUPPORTED_HOSTS

    @pytest.mark.parametrize("host", SUPPORTED_HOSTS, ids=str)
    def test_include_each_readme_host(self, host: str) -> None:
        assert host in HEADER[1:]


class TestTheRows:
    @pytest.mark.parametrize("row", REQUIRED_ROWS, ids=str)
    def test_include_each_required_row(self, row: str) -> None:
        assert row in BODY

    @pytest.mark.parametrize("row", REQUIRED_ROWS, ids=str)
    def test_fill_a_cell_for_every_host(self, row: str) -> None:
        cells = BODY.get(row, [])
        empty = [
            host for index, host in enumerate(HEADER[1:]) if index >= len(cells) or not cells[index]
        ]
        assert not empty, f"row {row!r} has no value for {empty}"

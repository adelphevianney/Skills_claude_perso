"""Tests de sonar_duplication."""

from __future__ import annotations

from sonar_duplication import consecutive_runs, find_duplicates, normalize_for_dup

BLOCK = [f"result_{index} = compute(value, {index})" for index in range(6)]


def numbered(lines: list[str]) -> list[tuple[int, str]]:
    return list(enumerate(lines))


def test_normalize_for_dup() -> None:
    assert normalize_for_dup("x  =  'abc' + 42 + 3.5") == "x = STR + NUM + NUM"


def test_consecutive_runs() -> None:
    assert list(consecutive_runs([1, 2, 3, 7, 9, 10])) == [(1, 3), (7, 7), (9, 10)]


def test_find_duplicates_across_files() -> None:
    file_code = {"a.py": numbered(["unique_a()", *BLOCK]), "b.py": numbered([*BLOCK, "unique_b()"])}

    dup_lines, blocks = find_duplicates(file_code, window=4)

    assert dup_lines == {"a.py": set(range(1, 7)), "b.py": set(range(6))}
    assert len(blocks) == 1
    assert blocks[0].to_dict() == {
        "lines": 6,
        "occurrences": [{"file": "a.py", "line": 2, "end_line": 7}, {"file": "b.py", "line": 1, "end_line": 6}],
    }


def test_find_duplicates_ignores_overlap_and_boilerplate() -> None:
    repeated = numbered(["same_call(x)"] * 5)
    imports = numbered(["import os", "import re", "}", "{"] * 2)
    dup_lines, blocks = find_duplicates({"a.py": repeated, "b.js": imports, "c.js": imports}, window=4)
    assert blocks == []
    assert dup_lines == {}

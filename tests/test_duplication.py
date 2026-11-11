"""Tests de tools.duplication."""

from __future__ import annotations

from pathlib import Path

from tools.duplication import find_duplication, normalized_code_lines

BLOCK = "\n".join(f"value_{index} = {index}" for index in range(10))


def test_normalized_code_lines_skips_blanks_and_comments() -> None:
    assert normalized_code_lines("  a = 1\n\n# commentaire\n    b  =  'x'  \n") == ["a = NUM", "b = STR"]


def test_blocks_differing_only_by_literals_are_duplicates(tmp_path: Path) -> None:
    first, second = tmp_path / "a.py", tmp_path / "b.py"
    first.write_text("\n".join(f"call_{index}('a', 1)" for index in range(10)), encoding="utf-8")
    second.write_text("\n".join(f'call_{index}("b", 2.5)' for index in range(10)), encoding="utf-8")
    assert find_duplication([first, second]).duplicated_lines == 20


def test_detects_block_duplicated_across_files(tmp_path: Path) -> None:
    first, second = tmp_path / "a.py", tmp_path / "b.py"
    first.write_text(BLOCK + "\nunique_a = 1\n", encoding="utf-8")
    second.write_text("    " + BLOCK.replace("\n", "\n    ") + "\n", encoding="utf-8")

    report = find_duplication([first, second])

    assert report.code_lines == 21
    assert report.duplicated_lines == 20
    assert report.duplicated_by_file == {str(first): 10, str(second): 10}
    assert round(report.ratio, 1) == 95.2


def test_no_duplication_below_window_size(tmp_path: Path) -> None:
    path = tmp_path / "a.py"
    path.write_text("x = 1\n" * 5, encoding="utf-8")
    report = find_duplication([path])
    assert report.duplicated_lines == 0


def test_empty_input_has_zero_ratio() -> None:
    assert find_duplication([]).ratio == 0.0

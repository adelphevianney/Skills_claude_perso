"""Tests de sonar_files."""

from __future__ import annotations

from pathlib import Path

import pytest
from sonar_files import code_lines, comment_prefixes, is_test_path, iter_files, language_of


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("tests/test_a.py", True),
        ("src/__tests__/a.js", True),
        ("src\\fixtures\\data.py", True),
        ("src/a.spec.ts", True),
        ("pkg/test_utils.py", True),
        ("src/app.py", False),
        ("src/latest.py", False),
    ],
)
def test_is_test_path(path: str, expected: bool) -> None:
    assert is_test_path(path) is expected


def test_language_of() -> None:
    assert language_of("a/B.JAVA") == "java"
    assert language_of("notes.txt") == "other"


@pytest.mark.parametrize(
    ("lang", "expected"),
    [
        ("python", ("#",)),
        ("ruby", ("#",)),
        ("sql", ("--",)),
        ("php", ("//", "#", "*", "/*")),
        ("go", ("//", "*", "/*")),
    ],
)
def test_comment_prefixes(lang: str, expected: tuple[str, ...]) -> None:
    assert comment_prefixes(lang) == expected


def test_code_lines_python_skips_docstrings_and_comments() -> None:
    source = [
        '"""Docstring',
        "sur deux lignes.",
        '"""',
        "",
        "# commentaire",
        "x = 1",
        '    """Docstring sur une ligne."""',
        '"""',
        "y = 2",
    ]
    assert code_lines(source, "python") == [(5, "x = 1")]


def test_code_lines_brace_languages_skip_block_comments() -> None:
    source = ["/* début", " * milieu", " fin */", "let a = 1; /* inline */", "// ligne", "/* seul */ b();"]
    assert code_lines(source, "javascript") == [(3, "let a = 1; /* inline */")]


def test_code_lines_sql() -> None:
    assert code_lines(["-- c", "SELECT 1;"], "sql") == [(1, "SELECT 1;")]


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x = 1\n", encoding="utf-8")
    return path


def test_iter_files_filters_directories_extensions_and_patterns(tmp_path: Path) -> None:
    kept = _touch(tmp_path / "src" / "app.py")
    _touch(tmp_path / "src" / "notes.txt")
    _touch(tmp_path / "src" / "lib.min.js")
    _touch(tmp_path / "node_modules" / "dep.js")
    _touch(tmp_path / ".hidden" / "h.py")
    _touch(tmp_path / "src" / "skip_me.py")
    explicit = _touch(tmp_path / "README.unknown")

    found = set(iter_files([str(tmp_path), str(explicit)], ["*skip_me*"]))

    assert found == {str(kept), str(explicit)}

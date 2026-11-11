"""Tests de sonar_model (format JSON)."""

from __future__ import annotations

from sonar_model import FileInfo, Issue


def test_file_info_omits_empty_optional_fields() -> None:
    info = FileInfo("a.py", "python", 3, 2, test=False)
    assert info.to_dict() == {
        "path": "a.py",
        "language": "python",
        "lines": 3,
        "ncloc": 2,
        "test": False,
        "functions": 0,
        "cyclomatic": 0,
        "max_cognitive": 0,
    }


def test_file_info_includes_optional_fields_when_set() -> None:
    info = FileInfo("a.py", "python", 3, 2, test=True, parse_error="SyntaxError", long_lines=1, duplicated_lines=2)
    data = info.to_dict()
    assert (data["parse_error"], data["long_lines"], data["duplicated_lines"]) == ("SyntaxError", 1, 2)


def test_issue_optional_fields() -> None:
    plain = Issue("R", "BUG", "MAJOR", "a.py", 1, "m")
    full = Issue("R", "BUG", "MAJOR", "a.py", 1, "m", effort_min=5, to_verify=True)
    assert "effort_min" not in plain.to_dict()
    assert "to_verify" not in plain.to_dict()
    assert (full.to_dict()["effort_min"], full.to_dict()["to_verify"]) == (5, True)

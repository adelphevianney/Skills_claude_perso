"""Tests de tools.quality_gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.quality_gate import (
    MAX_FILE_LINES,
    MAX_FUNCTION_LINES,
    analyze_file,
    collect_python_files,
    main,
    run_gate,
)

COMPLEX_FUNCTION = """
def tangled(a, b, c, d, e):
    if a:
        for x in b:
            if x:
                while c:
                    if d:
                        if e:
                            return 1
    return 0
"""


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_collect_python_files_excludes_tests_and_other_files(tmp_path: Path) -> None:
    kept = write(tmp_path / "pkg" / "mod.py", "")
    write(tmp_path / "pkg" / "tests" / "test_mod.py", "")
    write(tmp_path / "pkg" / "notes.md", "")
    single = write(tmp_path / "single.py", "")
    assert collect_python_files([tmp_path / "pkg", single]) == sorted([kept, single])


def test_clean_file_has_no_issue(tmp_path: Path) -> None:
    assert analyze_file(write(tmp_path / "ok.py", "def f():\n    return 1\n")) == []


def test_complex_function_reports_cognitive_and_nesting(tmp_path: Path) -> None:
    issues = analyze_file(write(tmp_path / "bad.py", COMPLEX_FUNCTION))
    assert {issue.rule for issue in issues} == {"SMELL-COGNITIVE", "SMELL-NESTING"}
    assert all(issue.line == 2 for issue in issues)
    assert "tangled()" in str(issues[0])


def test_long_function_and_long_file(tmp_path: Path) -> None:
    body = "".join(f"    v{index} = {index}\n" for index in range(MAX_FUNCTION_LINES))
    padding = "\n" * MAX_FILE_LINES
    issues = analyze_file(write(tmp_path / "long.py", f"def big():\n{body}{padding}"))
    assert {issue.rule for issue in issues} == {"SMELL-LONG-FN", "SMELL-LONG-FILE"}


def test_run_gate_fails_on_duplication(tmp_path: Path) -> None:
    block = "".join(f"value_{index} = {index}\n" for index in range(10))
    write(tmp_path / "a.py", block)
    write(tmp_path / "b.py", block)
    report = run_gate([tmp_path])
    assert not report.passed
    assert report.duplication_percent == 100.0
    assert report.to_dict()["passed"] is False


def test_main_passes_and_writes_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = write(tmp_path / "src" / "ok.py", "def f():\n    return 1\n")
    output = tmp_path / "report.json"
    assert main([str(source.parent), "--json", str(output)]) == 0
    assert "QUALITY GATE : PASSED" in capsys.readouterr().out
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is True


def test_main_fails_on_issues(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(tmp_path / "bad.py", COMPLEX_FUNCTION)
    assert main([str(tmp_path)]) == 1
    assert "QUALITY GATE : FAILED" in capsys.readouterr().out


def test_main_rejects_missing_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(tmp_path / "absent")]) == 2
    assert "introuvable" in capsys.readouterr().err

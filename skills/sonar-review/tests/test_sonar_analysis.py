"""Tests de sonar_analysis (analyse de bout en bout sur des fichiers temporaires)."""

from __future__ import annotations

from pathlib import Path

import pytest
from sonar_analysis import analyze, analyze_file, deduplicate, function_issues, pattern_issues, summarize
from sonar_model import FileInfo, FunctionStats, Issue

DATA_DIR = Path(__file__).resolve().parent / "data"
COMPLEX_PY = (DATA_DIR / "complex_sample.py.txt").read_text(encoding="utf-8")


def make_stats(
    *, length: int = 10, params: int = 2, cyclomatic: int = 1, cognitive: int = 0, nesting: int = 0
) -> FunctionStats:
    return FunctionStats("f", 3, length, params, cyclomatic, cognitive, nesting, returns=1)


def test_function_issues_respects_thresholds() -> None:
    assert function_issues(make_stats(), "a.py") == []
    issues = function_issues(
        make_stats(cognitive=30, cyclomatic=11, length=51, params=8, nesting=5),
        "a.py",
    )
    assert [(issue.rule, issue.severity, issue.effort_min) for issue in issues] == [
        ("SMELL-COGNITIVE", "CRITICAL", 20),
        ("SMELL-CYCLO", "MAJOR", 10),
        ("SMELL-LONG-FN", "MAJOR", 20),
        ("SMELL-PARAMS", "MAJOR", 20),
        ("SMELL-NESTING", "CRITICAL", 10),
    ]
    assert function_issues(make_stats(cognitive=16), "a.py")[0].severity == "MAJOR"


def test_approximate_flag_in_message() -> None:
    stats = FunctionStats("g", 1, 5, 1, 11, 0, 0, 0, approximate=True)
    assert function_issues(stats, "a.js")[0].message.endswith("(approx.)")


def test_pattern_issues_skip_security_in_tests_except_secrets() -> None:
    lines = (DATA_DIR / "patterns_sample.py.txt").read_text(encoding="utf-8").splitlines()
    in_source = {issue.rule for issue in pattern_issues(lines, "python", "src/a.py", is_test=False)}
    in_test = {issue.rule for issue in pattern_issues(lines, "python", "tests/a.py", is_test=True)}
    assert in_source == {"SEC-SECRET", "HOT-EXEC", "SMELL-PRINT"}
    assert in_test == {"SEC-SECRET", "SMELL-PRINT"}


def test_analyze_file_python_with_syntax_error() -> None:
    analysis = analyze_file("def broken(:\n    pass\n", "bad.py", "python")
    assert analysis.info.parse_error is not None
    assert [(issue.rule, issue.line) for issue in analysis.issues] == [("BUG-SYNTAX", 1)]


def test_analyze_file_sql_and_long_file() -> None:
    text = "SELECT 1;\n" * 751 + "-- " + "x" * 130 + "\n"
    analysis = analyze_file(text, "q.sql", "sql")
    assert analysis.info.functions == 0
    assert analysis.info.long_lines == 1
    assert [issue.rule for issue in analysis.issues] == ["SMELL-LONG-FILE"]


def test_deduplicate_keeps_first_issue() -> None:
    first = Issue("R", "BUG", "MAJOR", "a.py", 1, "premier")
    second = Issue("R", "BUG", "MAJOR", "a.py", 1, "second")
    assert deduplicate([first, second]) == [first]


def test_summarize_sorts_languages_and_estimates_debt() -> None:
    files = [
        FileInfo("b.js", "javascript", 10, 10, test=False),
        FileInfo("a.py", "python", 10, 10, test=True),
    ]
    issues = [
        Issue("SMELL-TODO", "CODE_SMELL", "INFO", "a.py", 1, "todo"),
        Issue("SMELL-PRINT", "CODE_SMELL", "MINOR", "a.py", 2, "print"),
        Issue("SMELL-DUP", "CODE_SMELL", "MAJOR", "a.py", 3, "dup", effort_min=10),
    ]
    summary = summarize(files, issues, duplicated_blocks=0)
    assert summary.languages == {"javascript": 10, "python": 10}
    assert summary.ncloc_tests == 10
    assert summary.issues_by_type == {"CODE_SMELL": {"INFO": 1, "MINOR": 1, "MAJOR": 1}}
    assert summary.smell_effort_min_estimate == 15
    assert summary.debt_ratio_pct_estimate == 2.5


def test_summarize_empty() -> None:
    summary = summarize([], [], 0)
    assert (summary.duplicated_lines_pct, summary.debt_ratio_pct_estimate) == (0.0, 0.0)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_analyze_project(tmp_path: Path) -> None:
    write(tmp_path / "src" / "app.py", COMPLEX_PY)
    write(tmp_path / "src" / "copy.py", COMPLEX_PY)
    write(tmp_path / "web" / "app.js", 'function f(a) {\n  if (a == 1) {\n    console.log("x");\n  }\n}\n')
    (tmp_path / "src" / "broken_link.py").symlink_to(tmp_path / "absent.py")

    result = analyze([str(tmp_path)], [], window=10)

    assert [info.path for info in result.files] == ["src/app.py", "src/copy.py", "web/app.js"]
    summary = result.summary
    assert (summary.files, summary.ncloc, summary.functions) == (3, 39, 3)
    assert summary.languages == {"python": 34, "javascript": 5}
    assert summary.duplicated_blocks == 1
    assert summary.duplicated_lines == 34
    rules = {issue.rule for issue in result.issues}
    assert {"SEC-SECRET", "HOT-EXEC", "BUG-SWALLOW", "BUG-MUTABLE-DEFAULT", "SMELL-TODO"} <= rules
    assert {"SMELL-COGNITIVE", "SMELL-PARAMS", "SMELL-DUP", "BUG-LOOSE-EQ", "SMELL-PRINT"} <= rules
    assert result.files[0].duplicated_lines == 17
    assert result.to_dict()["files"] == [info.to_dict() for info in result.files]


@pytest.mark.parametrize("use_cwd", [True, False])
def test_analyze_display_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, use_cwd: bool) -> None:
    write(tmp_path / "pkg" / "a.py", "x = 1\n")
    monkeypatch.chdir(tmp_path)
    paths = ["pkg", "pkg/a.py"] if use_cwd else [str(tmp_path / "pkg")]
    result = analyze(paths, [], window=10)
    assert [info.path for info in result.files] == (["pkg/a.py"] if use_cwd else ["a.py"])

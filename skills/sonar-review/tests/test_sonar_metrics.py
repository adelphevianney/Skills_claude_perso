"""Tests de l'interface en ligne de commande sonar_metrics."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

import pytest
from sonar_metrics import format_issue, has_blocking_issue, main
from sonar_model import Issue

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "sonar_metrics.py"


def test_format_issue() -> None:
    issue = Issue("HOT-EXEC", "SECURITY_HOTSPOT", "MAJOR", "a.py", 3, "eval(x)", to_verify=True)
    assert format_issue(issue) == "MAJOR    SECURITY_HOTSPOT HOT-EXEC           a.py:3  eval(x) [à vérifier]"


def test_main_writes_json_and_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.py").write_text("def f(x):\n    eval(x)\n    return x\n", encoding="utf-8")
    (source / "b.py").write_text("def g():\n    return 1\n", encoding="utf-8")
    output = tmp_path / "out.json"

    assert main([str(source), "--json", str(output), "--top", "1"]) == 0

    text = capsys.readouterr().out
    assert "Fichiers : 2 · NCLOC : 5 (dont tests : 0) · Fonctions : 2" in text
    assert "MAJOR    SECURITY_HOTSPOT HOT-EXEC           a.py:2  eval(x) [à vérifier]" in text
    assert "=== Top 1 fichiers par complexité cognitive max ===" in text
    assert text.rstrip().endswith("0  a.py (ncloc 3, cyclo 1, dup 0)")
    data = json.loads(output.read_text(encoding="utf-8"))
    assert set(data) == {"summary", "files", "issues", "duplications"}
    assert data["summary"]["issues_by_type"] == {"SECURITY_HOTSPOT": {"MAJOR": 1}}


@pytest.mark.parametrize(
    ("fail_on", "expected"),
    [(None, False), ("MAJOR", True), ("MINOR", True), ("CRITICAL", False)],
)
def test_has_blocking_issue(fail_on: str | None, expected: bool) -> None:
    issues = [Issue("R", "BUG", "MAJOR", "a.py", 1, "m"), Issue("T", "CODE_SMELL", "INFO", "a.py", 2, "t")]
    assert has_blocking_issue(issues, fail_on) is expected


def test_main_fail_on_sets_exit_code(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "a.py").write_text("def f(x):\n    eval(x)\n", encoding="utf-8")
    assert main([str(tmp_path), "--fail-on", "major"]) == 1
    assert main([str(tmp_path), "--fail-on", "critical"]) == 0
    capsys.readouterr()


def test_script_runs_as_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["sonar_metrics.py", str(tmp_path)])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert exit_info.value.code == 0

"""Quality gate local aligné sur les seuils « Sonar way » du skill sonar-review.

Usage : ``python -m tools.quality_gate <chemin> [<chemin> ...] [--json rapport.json]``

Contrôle le code Python (hors tests) : complexité cognitive, imbrication, longueur des
fonctions et des fichiers, duplication. Les autres règles (complexité cyclomatique,
nombre de paramètres et de retours, sécurité, typage, couverture) sont vérifiées
par ruff, mypy et pytest-cov : voir ``make check``.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from tools.cognitive import function_metrics, iter_functions
from tools.duplication import find_duplication

MAX_COGNITIVE = 15
MAX_NESTING = 4
MAX_FUNCTION_LINES = 50
MAX_FILE_LINES = 750
MAX_DUPLICATION_PERCENT = 3.0
EXCLUDED_DIRS = {"tests", "__pycache__", ".venv", "venv", "dist", "build"}


@dataclass(frozen=True)
class Issue:
    """Problème bloquant pour le quality gate."""

    rule: str
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line} [{self.rule}] {self.message}"


def collect_python_files(paths: Iterable[Path]) -> list[Path]:
    """Fichiers ``.py`` sous les chemins donnés, hors tests et dossiers techniques."""
    files: set[Path] = set()
    for path in paths:
        candidates = [path] if path.is_file() else path.rglob("*.py")
        files.update(
            candidate
            for candidate in candidates
            if candidate.suffix == ".py" and not EXCLUDED_DIRS.intersection(candidate.parts)
        )
    return sorted(files)


def analyze_file(path: Path) -> list[Issue]:
    """Issues de complexité et de taille pour un fichier."""
    source = path.read_text(encoding="utf-8")
    name = str(path)
    issues = []
    line_count = len(source.splitlines())
    if line_count > MAX_FILE_LINES:
        issues.append(Issue("SMELL-LONG-FILE", name, 1, f"{line_count} lignes (max {MAX_FILE_LINES})"))
    for node in iter_functions(ast.parse(source, filename=name)):
        metrics = function_metrics(node)
        checks = (
            ("SMELL-COGNITIVE", metrics.cognitive, MAX_COGNITIVE, "complexité cognitive"),
            ("SMELL-NESTING", metrics.nesting, MAX_NESTING, "imbrication"),
            ("SMELL-LONG-FN", metrics.length, MAX_FUNCTION_LINES, "lignes"),
        )
        issues.extend(
            Issue(rule, name, metrics.line, f"{metrics.name}() : {label} {value} (max {limit})")
            for rule, value, limit, label in checks
            if value > limit
        )
    return issues


@dataclass(frozen=True)
class GateReport:
    """Résultat du quality gate."""

    files: int
    code_lines: int
    duplication_percent: float
    duplicated_by_file: dict[str, int]
    issues: list[Issue]

    @property
    def passed(self) -> bool:
        """Vrai si aucune issue bloquante et duplication sous le seuil."""
        return not self.issues and self.duplication_percent <= MAX_DUPLICATION_PERCENT

    def to_dict(self) -> dict[str, object]:
        """Représentation sérialisable en JSON."""
        return {**asdict(self), "passed": self.passed}

    def to_text(self) -> str:
        """Rapport texte lisible."""
        lines = [str(issue) for issue in self.issues]
        lines.append(
            f"Fichiers : {self.files} | lignes de code : {self.code_lines} | "
            f"duplication : {self.duplication_percent} % (max {MAX_DUPLICATION_PERCENT} %)"
        )
        lines.append(f"Issues bloquantes : {len(self.issues)}")
        lines.append("QUALITY GATE : " + ("PASSED" if self.passed else "FAILED"))
        return "\n".join(lines)


def run_gate(paths: Sequence[Path]) -> GateReport:
    """Exécute l'analyse sur les chemins donnés."""
    files = collect_python_files(paths)
    duplication = find_duplication(files)
    return GateReport(
        files=len(files),
        code_lines=duplication.code_lines,
        duplication_percent=round(duplication.ratio, 2),
        duplicated_by_file=duplication.duplicated_by_file,
        issues=[issue for path in files for issue in analyze_file(path)],
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée en ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", type=Path, help="écrit le rapport JSON dans ce fichier")
    args = parser.parse_args(argv)

    missing = [str(path) for path in args.paths if not path.exists()]
    if missing:
        print(f"Chemin(s) introuvable(s) : {', '.join(missing)}", file=sys.stderr)
        return 2
    report = run_gate(args.paths)
    if args.json:
        args.json.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(report.to_text())
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())

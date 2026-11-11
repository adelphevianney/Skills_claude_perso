#!/usr/bin/env python3
"""Collecte de métriques façon SonarQube (bibliothèque standard uniquement).

Usage :
    python3 sonar_metrics.py <chemin> [<chemin> ...] [--json out.json] [--dup-min 10]
                             [--exclude motif ...] [--top 15] [--fail-on MINOR]

Calcule pour chaque fichier source :
  - NCLOC (lignes de code hors blancs et commentaires)
  - fonctions : complexité cyclomatique, complexité cognitive (Python : AST exact ;
    autres langages : heuristique à base d'accolades), longueur, paramètres, imbrication
  - duplication : fenêtres de N lignes normalisées identiques (défaut : 10)
  - motifs suspects : secrets, eval, catch vide, SQL concaténé, debug, TODO...

Les résultats sont des INDICES à vérifier, pas des verdicts.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from sonar_analysis import analyze
from sonar_model import AnalysisResult, Issue
from sonar_rules import SEV_ORDER, TYPE_ORDER

DEFAULT_WINDOW = 10
DEFAULT_TOP = 15
UNKNOWN_ORDER = 9


def _issue_sort_key(issue: Issue) -> tuple[int, int, str, int]:
    return (
        TYPE_ORDER.get(issue.type, UNKNOWN_ORDER),
        SEV_ORDER.get(issue.severity, UNKNOWN_ORDER),
        issue.file,
        issue.line,
    )


def format_issue(issue: Issue) -> str:
    """Ligne de rapport pour une issue."""
    flag = " [à vérifier]" if issue.to_verify else ""
    location = f"{issue.file}:{issue.line}"
    return f"{issue.severity:<8} {issue.type:<16} {issue.rule:<18} {location}  {issue.message}{flag}"


def render_text(result: AnalysisResult, top: int) -> str:
    """Rapport texte : métriques, issues triées par gravité, fichiers les plus complexes."""
    summary = result.summary
    languages = ", ".join(f"{name}={count}" for name, count in summary.languages.items())
    issues = sorted(result.issues, key=_issue_sort_key)
    lines = [
        "=== Métriques ===",
        f"Fichiers : {summary.files} · NCLOC : {summary.ncloc} (dont tests : {summary.ncloc_tests}) "
        f"· Fonctions : {summary.functions}",
        f"Langages : {languages}",
        f"Complexité cyclomatique totale : {summary.cyclomatic_total}",
        f"Duplication : {summary.duplicated_lines_pct} % ({summary.duplicated_lines} lignes, "
        f"{summary.duplicated_blocks} blocs)",
        f"Dette estimée (smells détectés auto) : {summary.smell_effort_min_estimate} min "
        f"· ratio ≈ {summary.debt_ratio_pct_estimate} %",
        "Issues détectées : " + json.dumps(summary.issues_by_type, ensure_ascii=False),
        "",
        f"=== Issues ({len(issues)}) ===",
        *(format_issue(issue) for issue in issues),
        "",
        f"=== Top {top} fichiers par complexité cognitive max ===",
    ]
    for info in sorted(result.files, key=lambda item: -item.max_cognitive)[:top]:
        lines.append(
            f"{info.max_cognitive:>4}  {info.path} (ncloc {info.ncloc}, cyclo {info.cyclomatic}, "
            f"dup {info.duplicated_lines})"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Analyseur des arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--json", help="écrit le résultat complet en JSON dans ce fichier")
    parser.add_argument(
        "--dup-min", type=int, default=DEFAULT_WINDOW, help="taille minimale (lignes) d'un bloc dupliqué"
    )
    parser.add_argument("--exclude", nargs="*", default=[], help="motifs glob à exclure")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP)
    parser.add_argument(
        "--fail-on",
        choices=list(SEV_ORDER),
        type=str.upper,
        help="code de sortie 1 si une issue atteint cette sévérité (usage en CI)",
    )
    return parser


def has_blocking_issue(issues: Iterable[Issue], fail_on: str | None) -> bool:
    """Vrai si une issue est au moins aussi grave que ``fail_on`` (jamais si ``fail_on`` est absent)."""
    if fail_on is None:
        return False
    limit = SEV_ORDER[fail_on]
    return any(SEV_ORDER.get(issue.severity, UNKNOWN_ORDER) <= limit for issue in issues)


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée en ligne de commande."""
    args = build_parser().parse_args(argv)
    result = analyze(args.paths, args.exclude, args.dup_min)
    if args.json:
        Path(args.json).write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(render_text(result, args.top))
    return 1 if has_blocking_issue(result.issues, args.fail_on) else 0


if __name__ == "__main__":
    sys.exit(main())

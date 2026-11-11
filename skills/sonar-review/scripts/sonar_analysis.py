"""Analyse d'un ensemble de fichiers : métriques, issues, duplication et synthèse."""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from sonar_brace import brace_functions
from sonar_duplication import find_duplicates
from sonar_files import CodeLine, code_lines, is_test_path, iter_files, language_of
from sonar_model import AnalysisResult, DuplicateBlock, FileInfo, FunctionStats, Issue, Summary
from sonar_python import python_functions
from sonar_rules import (
    BLOCKER,
    BUG,
    CODE_SMELL,
    CREDENTIAL_RULE_ID,
    CRITICAL,
    CRITICAL_COGNITIVE,
    INFO,
    MAJOR,
    RULES,
    SECURITY_TYPES,
    THRESHOLDS,
    Rule,
)

DEFAULT_EFFORT_MIN = 5
COGNITIVE_BASE_EFFORT_MIN = 5
CYCLOMATIC_EFFORT_MIN = 10
LONG_FUNCTION_EFFORT_MIN = 20
PARAMS_EFFORT_MIN = 20
NESTING_EFFORT_MIN = 10
LONG_FILE_EFFORT_MIN = 60
DUPLICATION_EFFORT_MIN = 10
MINUTES_PER_LINE = 30
MESSAGE_MAX_LENGTH = 160
_FIRST_NUMBER = re.compile(r"\d+")


@dataclass
class _FileAnalysis:
    """Résultat intermédiaire pour un fichier."""

    info: FileInfo
    code: list[CodeLine]
    issues: list[Issue] = field(default_factory=list)


def _functions_of(text: str, lines: Sequence[str], lang: str, info: FileInfo) -> list[FunctionStats]:
    """Fonctions du fichier ; renseigne ``info.parse_error`` si le Python est invalide."""
    if lang == "python":
        functions, error = python_functions(text)
        info.parse_error = error
        return functions
    if lang == "sql":
        return []
    return brace_functions(lines)


def _syntax_issue(path: str, error: str) -> Issue:
    match = _FIRST_NUMBER.search(error)
    line = int(match.group()) if match else 1
    return Issue("BUG-SYNTAX", BUG, BLOCKER, path, line, error)


def function_issues(func: FunctionStats, path: str) -> list[Issue]:
    """Code smells liés aux seuils de complexité et de taille d'une fonction."""
    approx = " (approx.)" if func.approximate else ""
    name = f"{func.name}()"
    limits = THRESHOLDS
    candidates = (
        (
            func.cognitive > limits["cognitive"],
            "SMELL-COGNITIVE",
            CRITICAL if func.cognitive > CRITICAL_COGNITIVE else MAJOR,
            f"Complexité cognitive de {name} = {func.cognitive} > {limits['cognitive']}{approx}",
            COGNITIVE_BASE_EFFORT_MIN + func.cognitive - limits["cognitive"],
        ),
        (
            func.cyclomatic > limits["cyclomatic"],
            "SMELL-CYCLO",
            MAJOR,
            f"Complexité cyclomatique de {name} = {func.cyclomatic} > {limits['cyclomatic']}{approx}",
            CYCLOMATIC_EFFORT_MIN,
        ),
        (
            func.length > limits["length"],
            "SMELL-LONG-FN",
            MAJOR,
            f"{name} fait {func.length} lignes > {limits['length']}",
            LONG_FUNCTION_EFFORT_MIN,
        ),
        (
            func.params > limits["params"],
            "SMELL-PARAMS",
            MAJOR,
            f"{name} a {func.params} paramètres > {limits['params']}",
            PARAMS_EFFORT_MIN,
        ),
        (
            func.nesting > limits["nesting"],
            "SMELL-NESTING",
            CRITICAL,
            f"Imbrication de profondeur {func.nesting} dans {name} > {limits['nesting']}",
            NESTING_EFFORT_MIN,
        ),
    )
    return [
        Issue(rule, CODE_SMELL, severity, path, func.line, message, effort_min=effort)
        for exceeded, rule, severity, message, effort in candidates
        if exceeded
    ]


def _rule_matches(rule: Rule, line: str, lang: str, is_test: bool) -> bool:
    """Le code de test est rarement exposé : seuls les secrets y sont signalés côté sécurité."""
    if not rule.applies_to(lang) or not rule.regex.search(line):
        return False
    return not (is_test and rule.type in SECURITY_TYPES and rule.rule_id != CREDENTIAL_RULE_ID)


def pattern_issues(lines: Sequence[str], lang: str, path: str, is_test: bool) -> list[Issue]:
    """Indices issus des motifs suspects, ligne par ligne."""
    return [
        Issue(rule.rule_id, rule.type, rule.severity, path, index + 1, raw.strip()[:MESSAGE_MAX_LENGTH], to_verify=True)
        for index, raw in enumerate(lines)
        for rule in RULES
        if _rule_matches(rule, raw, lang, is_test)
    ]


def analyze_file(text: str, path: str, lang: str) -> _FileAnalysis:
    """Analyse un fichier déjà lu ; ``path`` est le chemin affiché dans le rapport."""
    lines = text.splitlines()
    code = code_lines(lines, lang)
    info = FileInfo(path=path, language=lang, lines=len(lines), ncloc=len(code), test=is_test_path(path))
    functions = _functions_of(text, lines, lang, info)
    info.functions = len(functions)
    info.cyclomatic = sum(func.cyclomatic for func in functions)
    info.max_cognitive = max((func.cognitive for func in functions), default=0)
    info.long_lines = sum(len(raw) > THRESHOLDS["line_length"] for raw in lines)

    analysis = _FileAnalysis(info=info, code=code)
    if info.parse_error:
        analysis.issues.append(_syntax_issue(path, info.parse_error))
    for func in functions:
        analysis.issues.extend(function_issues(func, path))
    if len(lines) > THRESHOLDS["file_lines"]:
        message = f"Fichier de {len(lines)} lignes > {THRESHOLDS['file_lines']}"
        analysis.issues.append(
            Issue("SMELL-LONG-FILE", CODE_SMELL, MAJOR, path, 1, message, effort_min=LONG_FILE_EFFORT_MIN)
        )
    analysis.issues.extend(pattern_issues(lines, lang, path, info.test))
    return analysis


def duplication_issues(blocks: Iterable[DuplicateBlock]) -> list[Issue]:
    """Un code smell par bloc dupliqué, rattaché à sa première occurrence."""
    issues = []
    for block in blocks:
        other = f"{block.other.file}:{block.other.line}-{block.other.end_line}"
        message = f"Bloc de {block.lines} lignes de code dupliqué avec {other}"
        issues.append(
            Issue(
                "SMELL-DUP",
                CODE_SMELL,
                MAJOR,
                block.first.file,
                block.first.line,
                message,
                effort_min=DUPLICATION_EFFORT_MIN,
            )
        )
    return issues


def deduplicate(issues: Iterable[Issue]) -> list[Issue]:
    """Garde la première issue pour chaque triplet (règle, fichier, ligne)."""
    unique: dict[tuple[str, str, int], Issue] = {}
    for issue in issues:
        unique.setdefault((issue.rule, issue.file, issue.line), issue)
    return list(unique.values())


def _percent(part: int, total: int, digits: int) -> float:
    return round(100 * part / total, digits) if total else 0.0


def ncloc_by_language(files: Iterable[FileInfo]) -> dict[str, int]:
    """NCLOC par langage, du plus représenté au moins représenté (puis par nom)."""
    languages: Counter[str] = Counter()
    for info in files:
        languages[info.language] += info.ncloc
    return dict(sorted(languages.items(), key=lambda item: (-item[1], item[0])))


def count_by_type(issues: Iterable[Issue]) -> dict[str, dict[str, int]]:
    """Nombre d'issues par type puis par sévérité."""
    by_type: dict[str, dict[str, int]] = defaultdict(dict)
    for issue in issues:
        by_type[issue.type][issue.severity] = by_type[issue.type].get(issue.severity, 0) + 1
    return dict(by_type)


def smell_effort(issues: Iterable[Issue]) -> int:
    """Effort de remédiation estimé des code smells (hors INFO), en minutes."""
    smells = (issue for issue in issues if issue.type == CODE_SMELL and issue.severity != INFO)
    return sum(DEFAULT_EFFORT_MIN if issue.effort_min is None else issue.effort_min for issue in smells)


def summarize(files: Sequence[FileInfo], issues: Sequence[Issue], duplicated_blocks: int) -> Summary:
    """Synthèse chiffrée : volumes, duplication, issues par type et dette estimée."""
    ncloc = sum(info.ncloc for info in files)
    duplicated = sum(info.duplicated_lines for info in files)
    effort = smell_effort(issues)
    return Summary(
        files=len(files),
        ncloc=ncloc,
        ncloc_tests=sum(info.ncloc for info in files if info.test),
        languages=ncloc_by_language(files),
        functions=sum(info.functions for info in files),
        cyclomatic_total=sum(info.cyclomatic for info in files),
        duplicated_lines=duplicated,
        duplicated_lines_pct=_percent(duplicated, ncloc, 1),
        duplicated_blocks=duplicated_blocks,
        issues_by_type=count_by_type(issues),
        smell_effort_min_estimate=effort,
        debt_ratio_pct_estimate=_percent(effort, ncloc * MINUTES_PER_LINE, 2),
    )


def _display_base(paths: Sequence[str]) -> str:
    """Base des chemins affichés : le dossier analysé s'il est unique, sinon le répertoire courant."""
    if len(paths) == 1 and Path(paths[0]).is_dir():
        return paths[0]
    return str(Path.cwd())


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def analyze(paths: Sequence[str], excludes: Sequence[str], window: int) -> AnalysisResult:
    """Analyse complète des fichiers sources sous ``paths``."""
    base = _display_base(paths)
    analyses = []
    for path in sorted(set(iter_files(paths, excludes))):
        text = _read(path)
        if text is not None:
            analyses.append(analyze_file(text, os.path.relpath(path, base), language_of(path)))

    files = [analysis.info for analysis in analyses]
    dup_lines, blocks = find_duplicates({analysis.info.path: analysis.code for analysis in analyses}, window)
    for info in files:
        info.duplicated_lines = len(dup_lines.get(info.path, ()))

    issues = deduplicate([issue for analysis in analyses for issue in analysis.issues] + duplication_issues(blocks))
    return AnalysisResult(
        summary=summarize(files, issues, len(blocks)),
        files=files,
        issues=issues,
        duplications=blocks,
    )

"""Structures de données produites par l'analyse, sérialisables en JSON."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FunctionStats:
    """Métriques d'une fonction (``approximate`` : obtenues par heuristique)."""

    name: str
    line: int
    length: int
    params: int
    cyclomatic: int
    cognitive: int
    nesting: int
    returns: int
    approximate: bool = False


@dataclass(frozen=True)
class Issue:
    """Problème détecté ; ``to_verify`` marque un simple indice issu d'un motif."""

    rule: str
    type: str
    severity: str
    file: str
    line: int
    message: str
    effort_min: int | None = None
    to_verify: bool = False

    def to_dict(self) -> dict[str, object]:
        """Représentation JSON (les champs optionnels absents sont omis)."""
        data: dict[str, object] = {
            "rule": self.rule,
            "type": self.type,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "message": self.message,
        }
        if self.effort_min is not None:
            data["effort_min"] = self.effort_min
        if self.to_verify:
            data["to_verify"] = True
        return data


@dataclass
class FileInfo:
    """Métriques d'un fichier."""

    path: str
    language: str
    lines: int
    ncloc: int
    test: bool
    functions: int = 0
    cyclomatic: int = 0
    max_cognitive: int = 0
    parse_error: str | None = None
    long_lines: int = 0
    duplicated_lines: int = 0

    def to_dict(self) -> dict[str, object]:
        """Représentation JSON (les compteurs optionnels nuls sont omis)."""
        data: dict[str, object] = {
            "path": self.path,
            "language": self.language,
            "lines": self.lines,
            "ncloc": self.ncloc,
            "test": self.test,
        }
        if self.parse_error is not None:
            data["parse_error"] = self.parse_error
        data.update(functions=self.functions, cyclomatic=self.cyclomatic, max_cognitive=self.max_cognitive)
        if self.long_lines:
            data["long_lines"] = self.long_lines
        if self.duplicated_lines:
            data["duplicated_lines"] = self.duplicated_lines
        return data


@dataclass(frozen=True)
class Occurrence:
    """Emplacement d'un bloc dupliqué (lignes numérotées à partir de 1)."""

    file: str
    line: int
    end_line: int


@dataclass(frozen=True)
class DuplicateBlock:
    """Bloc de code présent à deux endroits."""

    lines: int
    first: Occurrence
    other: Occurrence

    def to_dict(self) -> dict[str, object]:
        """Représentation JSON."""
        occurrences = [vars(self.first), vars(self.other)]
        return {"lines": self.lines, "occurrences": [dict(occurrence) for occurrence in occurrences]}


@dataclass
class Summary:
    """Synthèse chiffrée de l'analyse."""

    files: int
    ncloc: int
    ncloc_tests: int
    languages: dict[str, int]
    functions: int
    cyclomatic_total: int
    duplicated_lines: int
    duplicated_lines_pct: float
    duplicated_blocks: int
    issues_by_type: dict[str, dict[str, int]]
    smell_effort_min_estimate: int
    debt_ratio_pct_estimate: float
    note: str = (
        "Indices automatiques : à confirmer par revue manuelle. "
        "Les fonctions non-Python sont analysées par heuristique."
    )


@dataclass
class AnalysisResult:
    """Résultat complet de l'analyse."""

    summary: Summary
    files: list[FileInfo] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    duplications: list[DuplicateBlock] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Représentation JSON."""
        return {
            "summary": vars(self.summary),
            "files": [info.to_dict() for info in self.files],
            "issues": [issue.to_dict() for issue in self.issues],
            "duplications": [block.to_dict() for block in self.duplications],
        }

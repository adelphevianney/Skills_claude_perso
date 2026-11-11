"""Détection des lignes dupliquées (blocs de N lignes normalisées identiques)."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MIN_LINES = 10
_COMMENT_PREFIX = "#"
MIN_OCCURRENCES = 2


@dataclass(frozen=True)
class DuplicationReport:
    """Synthèse de la duplication sur un ensemble de fichiers."""

    code_lines: int
    duplicated_lines: int
    duplicated_by_file: dict[str, int]

    @property
    def ratio(self) -> float:
        """Pourcentage de lignes de code dupliquées."""
        return 100 * self.duplicated_lines / self.code_lines if self.code_lines else 0.0


def normalized_code_lines(source: str) -> list[str]:
    """Lignes de code significatives, sans indentation ni commentaires de ligne."""
    lines = (line.strip() for line in source.splitlines())
    return [line for line in lines if line and not line.startswith(_COMMENT_PREFIX)]


def _window_hash(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def find_duplication(files: Iterable[Path], min_lines: int = DEFAULT_MIN_LINES) -> DuplicationReport:
    """Repère les fenêtres de ``min_lines`` lignes identiques présentes au moins deux fois."""
    contents = {str(path): normalized_code_lines(path.read_text(encoding="utf-8")) for path in files}
    windows: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for name, lines in contents.items():
        for start in range(len(lines) - min_lines + 1):
            windows[_window_hash(lines[start : start + min_lines])].append((name, start))

    duplicated: dict[str, set[int]] = defaultdict(set)
    for occurrences in windows.values():
        if len(occurrences) < MIN_OCCURRENCES:
            continue
        for name, start in occurrences:
            duplicated[name].update(range(start, start + min_lines))

    by_file = {name: len(indexes) for name, indexes in duplicated.items()}
    return DuplicationReport(
        code_lines=sum(len(lines) for lines in contents.values()),
        duplicated_lines=sum(by_file.values()),
        duplicated_by_file=by_file,
    )

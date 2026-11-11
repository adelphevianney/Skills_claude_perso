"""Détection des blocs dupliqués entre fichiers (et au sein d'un même fichier)."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence

from sonar_files import CodeLine
from sonar_model import DuplicateBlock, Occurrence

MIN_MEANINGFUL_RATIO = 0.6
MIN_MEANINGFUL_LENGTH = 3
MIN_OCCURRENCES = 2

_STRING_LITERAL = re.compile(r"""(['"`])(?:\\.|(?!\1).)*\1""")
_NUMBER = re.compile(r"\b\d+(\.\d+)?\b")
_WHITESPACE = re.compile(r"\s+")
_BOILERPLATE = re.compile(r"^(import|from|using|#include|package|\}|\{|\)|\]|end)\b")

PairKey = tuple[str, str, int]  # (fichier A, fichier B, décalage de B par rapport à A)


def normalize_for_dup(line: str) -> str:
    """Neutralise littéraux et espaces pour comparer la structure des lignes."""
    line = _STRING_LITERAL.sub("STR", line)
    line = _NUMBER.sub("NUM", line)
    return _WHITESPACE.sub(" ", line)


def _is_meaningful(chunk: Sequence[str], window: int) -> bool:
    """Écarte les fenêtres composées surtout d'imports ou de ponctuation."""
    meaningful = [line for line in chunk if len(line) > MIN_MEANINGFUL_LENGTH and not _BOILERPLATE.match(line)]
    return len(meaningful) >= window * MIN_MEANINGFUL_RATIO


def _index_windows(file_code: Mapping[str, Sequence[CodeLine]], window: int) -> dict[str, list[tuple[str, int]]]:
    """Empreinte de chaque fenêtre significative → positions ``(fichier, début)``."""
    index: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for path, lines in file_code.items():
        normalized = [normalize_for_dup(text) for _, text in lines]
        for start in range(len(normalized) - window + 1):
            chunk = normalized[start : start + window]
            if _is_meaningful(chunk, window):
                digest = hashlib.sha256("\n".join(chunk).encode()).hexdigest()
                index[digest].append((path, start))
    return index


def _pair_starts(index: Mapping[str, list[tuple[str, int]]], window: int) -> dict[PairKey, set[int]]:
    """Regroupe les fenêtres identiques par paire de fichiers et décalage."""
    pairs: dict[PairKey, set[int]] = defaultdict(set)
    for positions in index.values():
        if len(positions) < MIN_OCCURRENCES:
            continue
        ordered = sorted(positions)
        for position, (path_a, start_a) in enumerate(ordered):
            for path_b, start_b in ordered[position + 1 :]:
                overlapping = path_a == path_b and start_b - start_a < window
                if not overlapping:
                    pairs[(path_a, path_b, start_b - start_a)].add(start_a)
    return pairs


def consecutive_runs(starts: Sequence[int]) -> Iterator[tuple[int, int]]:
    """Plages ``(premier, dernier)`` d'entiers consécutifs dans une liste triée."""
    first = previous = starts[0]
    for start in starts[1:]:
        if start != previous + 1:
            yield first, previous
            first = start
        previous = start
    yield first, previous


def find_duplicates(
    file_code: Mapping[str, Sequence[CodeLine]], window: int
) -> tuple[dict[str, set[int]], list[DuplicateBlock]]:
    """Fenêtres de ``window`` lignes normalisées identiques, regroupées en blocs contigus.

    Renvoie les index de lignes dupliquées par fichier et les blocs, du plus grand au plus petit.
    """
    dup_lines: dict[str, set[int]] = defaultdict(set)
    blocks = []
    for (path_a, path_b, offset), starts in _pair_starts(_index_windows(file_code, window), window).items():
        lines_a, lines_b = file_code[path_a], file_code[path_b]
        for first, last in consecutive_runs(sorted(starts)):
            end = last + window - 1
            dup_lines[path_a].update(lines_a[index][0] for index in range(first, end + 1))
            dup_lines[path_b].update(lines_b[index + offset][0] for index in range(first, end + 1))
            blocks.append(
                DuplicateBlock(
                    lines=end - first + 1,
                    first=Occurrence(path_a, lines_a[first][0] + 1, lines_a[end][0] + 1),
                    other=Occurrence(path_b, lines_b[first + offset][0] + 1, lines_b[end + offset][0] + 1),
                )
            )
    blocks.sort(key=lambda block: -block.lines)
    return dup_lines, blocks

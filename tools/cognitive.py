"""Complexité cognitive et profondeur d'imbrication des fonctions Python.

Implémentation simplifiée de la spécification « Cognitive Complexity » de SonarSource :

* +1 (plus le niveau d'imbrication) pour ``if``, ``for``, ``while``, ``except``,
  ``match``, expression conditionnelle ;
* +1 sans pénalité d'imbrication pour ``elif``, ``else`` et chaque suite
  d'opérateurs booléens ;
* les fonctions et lambdas imbriquées augmentent le niveau d'imbrication.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
_LOOPS = (ast.For, ast.AsyncFor, ast.While)
_NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


@dataclass(frozen=True)
class FunctionMetrics:
    """Métriques d'une fonction."""

    name: str
    line: int
    length: int
    cognitive: int
    nesting: int


class _Scorer:
    """Parcourt le corps d'une fonction en cumulant score et imbrication maximale."""

    def __init__(self) -> None:
        self.score = 0
        self.max_nesting = 0

    def visit_body(self, nodes: list[ast.stmt], nesting: int) -> None:
        for node in nodes:
            self.visit(node, nesting)

    def visit(self, node: ast.AST, nesting: int) -> None:
        if isinstance(node, ast.If):
            self._visit_if(node, nesting)
        elif isinstance(node, _LOOPS):
            self._structure(nesting)
            self.visit(node.target if isinstance(node, ast.For | ast.AsyncFor) else node.test, nesting)
            self._nested_block(node.body, nesting)
            self._else_block(node.orelse, nesting)
        elif isinstance(node, ast.Try | ast.TryStar):
            self._visit_try(node, nesting)
        elif isinstance(node, ast.Match):
            self._structure(nesting)
            self.visit(node.subject, nesting)
            for case in node.cases:
                self._nested_block(case.body, nesting)
        elif isinstance(node, ast.IfExp):
            self._structure(nesting)
            self._children(node, nesting)
        elif isinstance(node, ast.BoolOp):
            self.score += 1
            self._children(node, nesting)
        elif isinstance(node, _NESTED_SCOPES):
            self._children(node, nesting + 1)
        else:
            self._children(node, nesting)

    def _children(self, node: ast.AST, nesting: int) -> None:
        for child in ast.iter_child_nodes(node):
            self.visit(child, nesting)

    def _structure(self, nesting: int) -> None:
        self.score += 1 + nesting
        self.max_nesting = max(self.max_nesting, nesting + 1)

    def _nested_block(self, body: list[ast.stmt], nesting: int) -> None:
        self.visit_body(body, nesting + 1)

    def _else_block(self, orelse: list[ast.stmt], nesting: int) -> None:
        if orelse:
            self.score += 1
            self._nested_block(orelse, nesting)

    def _visit_if(self, node: ast.If, nesting: int, is_elif: bool = False) -> None:
        if is_elif:
            self.score += 1
        else:
            self._structure(nesting)
        self.visit(node.test, nesting)
        self._nested_block(node.body, nesting)
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            self._visit_if(node.orelse[0], nesting, is_elif=True)
        else:
            self._else_block(node.orelse, nesting)

    def _visit_try(self, node: ast.Try | ast.TryStar, nesting: int) -> None:
        self.visit_body(node.body, nesting)
        for handler in node.handlers:
            self._structure(nesting)
            self._nested_block(handler.body, nesting)
        self._else_block(node.orelse, nesting)
        self.visit_body(node.finalbody, nesting)


def function_metrics(node: FunctionNode) -> FunctionMetrics:
    """Calcule les métriques d'une fonction (hors fonctions qu'elle contient)."""
    scorer = _Scorer()
    scorer.visit_body(node.body, 0)
    end_line = node.end_lineno or node.lineno
    return FunctionMetrics(
        name=node.name,
        line=node.lineno,
        length=end_line - node.lineno + 1,
        cognitive=scorer.score,
        nesting=scorer.max_nesting,
    )


def iter_functions(tree: ast.AST) -> Iterator[FunctionNode]:
    """Toutes les fonctions et méthodes d'un module, y compris imbriquées."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            yield node

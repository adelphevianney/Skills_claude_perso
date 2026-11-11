"""Métriques exactes des fonctions Python, calculées sur l'AST."""

from __future__ import annotations

import ast
import functools

from sonar_model import FunctionStats

_IMPLICIT_RECEIVERS = frozenset({"self", "cls"})


class PyComplexity:
    """Cumule complexités cyclomatique et cognitive, imbrication et ``return`` d'un corps de fonction.

    Règles de la complexité cognitive : +1 (plus l'imbrication) par structure de contrôle,
    +1 sans pénalité pour ``elif``/``else`` et chaque suite d'opérateurs booléens ;
    les fonctions et lambdas imbriquées augmentent l'imbrication.
    """

    def __init__(self) -> None:
        self.cyclo = 1
        self.cognitive = 0
        self.max_nesting = 0
        self.returns = 0
        self._nest = 0

    @functools.singledispatchmethod
    def visit(self, node: ast.AST) -> None:
        """Visite un nœud en appliquant la règle propre à son type."""
        self.generic_visit(node)

    def generic_visit(self, node: ast.AST) -> None:
        """Visite les enfants d'un nœud sans rien comptabiliser."""
        for child in ast.iter_child_nodes(node):
            self.visit(child)

    def _enter(self) -> None:
        self._nest += 1
        self.max_nesting = max(self.max_nesting, self._nest)

    def _visit_nested(self, node: ast.AST) -> None:
        self._enter()
        self.generic_visit(node)
        self._nest -= 1

    @visit.register
    def _visit_structure(self, node: ast.For | ast.AsyncFor | ast.While | ast.IfExp) -> None:
        self.cyclo += 1
        self.cognitive += 1 + self._nest
        self._visit_nested(node)

    @visit.register
    def _visit_if(self, node: ast.If) -> None:
        self.cyclo += 1
        self.cognitive += 1 + self._nest
        self._enter()
        self.visit(node.test)
        for statement in node.body:
            self.visit(statement)
        self._nest -= 1
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            self.cognitive -= self._nest  # elif : pas de pénalité d'imbrication
            self.visit(node.orelse[0])
        elif node.orelse:
            self.cognitive += 1
            self._nest += 1
            for statement in node.orelse:
                self.visit(statement)
            self._nest -= 1

    @visit.register
    def _visit_try(self, node: ast.Try | ast.TryStar) -> None:
        handlers = len(node.handlers)
        self.cyclo += handlers
        self.cognitive += handlers * (1 + self._nest)
        self._visit_nested(node)

    @visit.register
    def _visit_bool_op(self, node: ast.BoolOp) -> None:
        self.cyclo += len(node.values) - 1
        self.cognitive += 1
        self.generic_visit(node)

    @visit.register
    def _visit_comprehension(self, node: ast.comprehension) -> None:
        self.cyclo += 1 + len(node.ifs)
        self.generic_visit(node)

    @visit.register
    def _visit_return(self, node: ast.Return) -> None:
        self.returns += 1
        self.generic_visit(node)

    @visit.register
    def _visit_scope(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda) -> None:
        """Fonction ou lambda imbriquée : augmente l'imbrication sans compter."""
        self._nest += 1
        self.generic_visit(node)
        self._nest -= 1


def count_params(arguments: ast.arguments) -> int:
    """Nombre de paramètres déclarés, hors ``self``/``cls``."""
    count = (
        len(arguments.posonlyargs)
        + len(arguments.args)
        + len(arguments.kwonlyargs)
        + int(arguments.vararg is not None)
        + int(arguments.kwarg is not None)
    )
    if arguments.args and arguments.args[0].arg in _IMPLICIT_RECEIVERS:
        count -= 1
    return count


def function_stats(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionStats:
    """Métriques d'une fonction Python."""
    visitor = PyComplexity()
    for statement in node.body:
        visitor.visit(statement)
    return FunctionStats(
        name=node.name,
        line=node.lineno,
        length=(node.end_lineno or node.lineno) - node.lineno + 1,
        params=count_params(node.args),
        cyclomatic=visitor.cyclo,
        cognitive=visitor.cognitive,
        nesting=visitor.max_nesting,
        returns=visitor.returns,
    )


def python_functions(source: str) -> tuple[list[FunctionStats], str | None]:
    """Métriques de toutes les fonctions d'un module, ou message d'erreur de syntaxe."""
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [], f"SyntaxError ligne {error.lineno}: {error.msg}"
    return [
        function_stats(node) for node in ast.walk(tree) if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ], None

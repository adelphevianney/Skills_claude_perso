"""Tests de tools.cognitive (valeurs de référence de la spécification SonarSource)."""

from __future__ import annotations

import ast
import textwrap

import pytest

from tools.cognitive import FunctionMetrics, function_metrics, iter_functions


def metrics_of(source: str) -> FunctionMetrics:
    tree = ast.parse(textwrap.dedent(source))
    return function_metrics(next(iter_functions(tree)))


def test_linear_function_scores_zero() -> None:
    metrics = metrics_of("def f(a):\n    return a + 1\n")
    assert (metrics.cognitive, metrics.nesting, metrics.length) == (0, 0, 2)


def test_if_elif_else_chain() -> None:
    source = """
    def f(x):
        if x > 0:
            return 1
        elif x < 0:
            return -1
        else:
            return 0
    """
    assert metrics_of(source).cognitive == 3


def test_nesting_increments_score() -> None:
    source = """
    def f(items):
        for item in items:
            if item:
                while item:
                    item -= 1
    """
    metrics = metrics_of(source)
    assert metrics.cognitive == 1 + 2 + 3
    assert metrics.nesting == 3


def test_try_except_else_finally_and_loop_else() -> None:
    source = """
    def f(items):
        try:
            for item in items:
                pass
            else:
                pass
        except ValueError:
            pass
        except KeyError:
            pass
        else:
            pass
        finally:
            pass
    """
    assert metrics_of(source).cognitive == 1 + 1 + 1 + 1 + 1


def test_boolean_sequences_ternary_and_match() -> None:
    source = """
    def f(a, b, c):
        value = a if b and c or a else b
        match value:
            case 1:
                if a:
                    pass
            case _:
                pass
    """
    # ternaire 1, `and` 1, `or` 1, match 1, if imbriqué 2
    assert metrics_of(source).cognitive == 6


def test_nested_function_increases_nesting() -> None:
    source = """
    def outer(a):
        def inner():
            if a:
                return 1
            return 0
        return inner
    """
    tree = ast.parse(textwrap.dedent(source))
    by_name = {node.name: function_metrics(node) for node in iter_functions(tree)}
    assert by_name["outer"].cognitive == 2
    assert by_name["inner"].cognitive == 1


@pytest.mark.parametrize("keyword", ["def", "async def"])
def test_iter_functions_finds_sync_and_async(keyword: str) -> None:
    tree = ast.parse(f"class A:\n    {keyword} m(self):\n        pass\n")
    assert [node.name for node in iter_functions(tree)] == ["m"]

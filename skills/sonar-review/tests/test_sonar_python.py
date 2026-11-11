"""Tests de sonar_python."""

from __future__ import annotations

import textwrap

from sonar_python import python_functions


def stats(source: str) -> dict[str, dict[str, int]]:
    functions, error = python_functions(textwrap.dedent(source))
    assert error is None
    return {
        func.name: {
            "cyclo": func.cyclomatic,
            "cog": func.cognitive,
            "nest": func.nesting,
            "params": func.params,
            "returns": func.returns,
        }
        for func in functions
    }


def test_linear_function() -> None:
    assert stats("def f(a, b):\n    return a\n")["f"] == {"cyclo": 1, "cog": 0, "nest": 0, "params": 2, "returns": 1}


def test_if_elif_else_and_boolean_operators() -> None:
    source = """
    def f(x, y):
        if x and y or x:
            return 1
        elif x:
            return 2
        else:
            return 3
    """
    assert stats(source)["f"] == {"cyclo": 5, "cog": 5, "nest": 1, "params": 2, "returns": 3}


def test_nested_loops_try_and_comprehension() -> None:
    source = """
    def f(items):
        try:
            for item in items:
                while item:
                    item = [i for i in item if i if i > 1]
        except ValueError:
            pass
        except KeyError:
            pass
        return items if items else None
    """
    assert stats(source)["f"] == {"cyclo": 9, "cog": 8, "nest": 3, "params": 1, "returns": 1}


def test_nested_function_lambda_and_async() -> None:
    source = """
    class A:
        async def method(self, *args, key=None, **kwargs):
            async for value in args:
                handler = lambda v: v if v else 0
            def inner():
                if key:
                    return 1
            return inner
    """
    result = stats(source)
    assert result["method"] == {"cyclo": 4, "cog": 6, "nest": 3, "params": 3, "returns": 2}
    assert result["inner"]["cog"] == 1


def test_syntax_error_is_reported() -> None:
    functions, error = python_functions("def broken(:\n    pass\n")
    assert functions == []
    assert error is not None
    assert error.startswith("SyntaxError ligne 1")

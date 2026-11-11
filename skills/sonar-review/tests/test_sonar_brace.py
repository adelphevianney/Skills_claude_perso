"""Tests de sonar_brace."""

from __future__ import annotations

from sonar_brace import brace_functions, strip_strings

JS_SOURCE = """\
export async function handler(req, res, a) {
  if (req.x && a || res) {
    for (const i of a) {
      if (i ? 1 : 0) {
        return "if (x) { y }";
      }
    }
  } else {
    try { run(); } catch (err) { log(err); }
  }
  return a ?? res;
}
const arrow = async (a, b) => {
  return a;
};
if (cond) {
  call();
}
function unterminated(a) {
  if (a) {
"""


def test_strip_strings_blanks_literals() -> None:
    assert strip_strings("""a = "x{" + 'y}' + `z`;""") == 'a = "" + "" + "";'


def test_brace_functions_detects_functions_and_metrics() -> None:
    functions = {func.name: func for func in brace_functions(JS_SOURCE.splitlines())}

    assert set(functions) == {"handler", "arrow", "unterminated"}
    handler = functions["handler"]
    assert (handler.line, handler.length, handler.params) == (1, 12, 3)
    assert (handler.cyclomatic, handler.cognitive, handler.nesting, handler.returns) == (9, 10, 3, 2)
    assert handler.approximate
    assert (functions["arrow"].params, functions["arrow"].returns) == (2, 1)
    assert functions["unterminated"].length == 3

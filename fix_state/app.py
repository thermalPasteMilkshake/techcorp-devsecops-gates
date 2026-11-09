"""FIX-STATE app.py - eval() replaced with a safe evaluator, system prompt
moved to an environment variable."""

import ast
import os
import operator

SYSTEM_PROMPT_ENV = os.environ.get("SYSTEM_PROMPT", "")

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def compute(expr):
    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        raise ValueError("unsupported expression")

    return _eval(ast.parse(expr, mode="eval").body)


def main():
    print(SYSTEM_PROMPT_ENV)
    print(compute("1+1"))


if __name__ == "__main__":
    main()

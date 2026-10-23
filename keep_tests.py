#!/usr/bin/env python3
"""Checks that an agent kept the original tests while adding its own.

    keep_tests.py ORIGINAL CURRENT

Every top-level function and class in ORIGINAL must still be in CURRENT
(methods compared one by one, so new methods may be added to a class). A test
may gain statements at the end: its signature and decorators, and its original
statements in order, must be unchanged. Anything appended runs after the
original assertions, so it can only make the test stricter. Extra code in
CURRENT is fine: the tasks ask for new tests.
"""
import ast
import sys


def defs(path):
    src = open(path).read()
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[f"{node.name}.{m.name}"] = m
    return out


def kept(old, new):
    """`new` is `old`, possibly with statements appended to its body."""
    if new is None or type(old) is not type(new):
        return False
    same = lambda a, b: [ast.dump(x) for x in a] == [ast.dump(x) for x in b]
    return (
        ast.dump(old.args) == ast.dump(new.args)
        and same(old.decorator_list, new.decorator_list)
        and same(old.body, new.body[: len(old.body)])
    )


original, current = defs(sys.argv[1]), defs(sys.argv[2])
bad = [n for n, d in original.items() if not kept(d, current.get(n))]
if bad:
    print(f"{sys.argv[2]}: existing tests removed or changed: {', '.join(bad)}")
    sys.exit(1)

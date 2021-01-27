import time
from timeit import timeit

import pytest
from collections import namedtuple
from eunomia._eval import try_parse_expression, asteval_interpret_expr
from eunomia._eval import ParserError, ExpressionSemicolonError, UnsupportedLanguageFeatureError, NotExpressionError, MalformedPythonError


def test_parse():
    try_parse_expression('1')
    try_parse_expression('1 + 2')
    try_parse_expression('"asdf" + "fdsa"')
    try_parse_expression('f"as{1}df" + "fdsa"')
    try_parse_expression('config["asdf"]["fdsa"]["cheese"]')
    try_parse_expression('config.asdf.fdsa')
    try_parse_expression('[i for i in range(10)]')

    with pytest.raises(ExpressionSemicolonError):
        try_parse_expression('[1 + 2];')
    with pytest.raises(NotExpressionError):
        try_parse_expression('[1 + 2];')
    with pytest.raises(ParserError):
        try_parse_expression('[1 + 2];')

    with pytest.raises(MalformedPythonError):
        try_parse_expression('def asdf():\n    "full indent"\n  "partial indent"')
    with pytest.raises(MalformedPythonError):
        try_parse_expression('$2341(')
    with pytest.raises(ParserError):
        try_parse_expression('$2341(')

    try_parse_expression('1 + 2')
    with pytest.raises(NotExpressionError):
        try_parse_expression('1 + 2;')
    with pytest.raises(ParserError):
        try_parse_expression('1 + 2;')

    with pytest.raises(NotExpressionError):
        try_parse_expression('a = [1 + 2]')
    with pytest.raises(NotExpressionError):
        try_parse_expression('a = [1 + 2]; b=2')
    with pytest.raises(NotExpressionError):
        try_parse_expression('a = [1 + 2]\nb=2')
    with pytest.raises(NotExpressionError):
        try_parse_expression('def func(): 1 + 2')

    # these are not supported by asteval but should be
    # supported here because they are expressions.
    try_parse_expression('lambda: 1 + 2')
    try_parse_expression('lambda: 1 + 2')
    try_parse_expression('f"as{1}ds"')
    try_parse_expression('f"as{1}ds" + "fdsa"')


def test_eval():
    assert asteval_interpret_expr('1') == 1
    assert asteval_interpret_expr('1 + 2') == 3
    assert asteval_interpret_expr('"asdf" + "fdsa"') == 'asdffdsa'
    assert asteval_interpret_expr('[i for i in range(3)]') == [0, 1, 2]
    assert asteval_interpret_expr('tuple([i for i in range(3)])') == (0, 1, 2)

    with pytest.raises(UnsupportedLanguageFeatureError):
        asteval_interpret_expr('f"as{1}df" + "fdsa"')
    with pytest.raises(UnsupportedLanguageFeatureError):
        asteval_interpret_expr('lambda: 1 + 2')
    with pytest.raises(ExpressionSemicolonError):
        asteval_interpret_expr('1 + 2;')
    with pytest.raises(NotExpressionError):
        asteval_interpret_expr('a = 1 + 2')
    with pytest.raises(MalformedPythonError):
        asteval_interpret_expr('%adsf@')

    assert asteval_interpret_expr('config["key"][1]', usersyms=dict(config={'key': [1, 2, 3]})) == 2
    assert asteval_interpret_expr('config.asdf["key"]', usersyms=dict(config=namedtuple('Test', 'asdf')(asdf={'key': 2}))) == 2


def test_interpret_timeit():
    def ave_timeit_ms(expr, n=100):
        return f'{timeit(expr, number=n) / n * 1000:1.3f}ms'

    expr = 'tuple([i for i in range(3)])'

    def check_expr():
        try_parse_expression(expr)

    def check_invalid_expr():
        try:
            try_parse_expression(expr + ';')
        except:
            pass

    def interpret_expr():
        assert asteval_interpret_expr(expr) == (0, 1, 2)

    print()
    print('Check Expr Time:', ave_timeit_ms(check_expr))
    print('Check Invalid Expr Time:', ave_timeit_ms(check_invalid_expr))
    print('Interpret Time:', ave_timeit_ms(interpret_expr))

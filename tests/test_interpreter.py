from typing import Callable, Any
import pytest
import ast
from eunomia._interpreter import Interpreter, BasicInterpreter, UnsupportedLanguageFeatureError, DisabledLanguageFeatureError


# ========================================================================= #
# Fixtures                                                                  #
# ========================================================================= #


@pytest.fixture()
def interpret() -> Callable[[str], Any]:
    return BasicInterpreter().interpret


@pytest.fixture()
def interpret_nonstrict() -> Callable[[str], Any]:
    return BasicInterpreter(
        allow_nested_unary=True,
        allow_numerical_unary_on_bool=True,
        allow_chained_comparisons=True,
    ).interpret


# ========================================================================= #
# Basic Expressions + Literals                                              #
# ========================================================================= #


# https://docs.python.org/3/reference/expressions.html#literals
def test_interpret_literals(interpret):
    # stringliteral | bytesliteral
    assert interpret('"asdf"') == "asdf"
    assert interpret('"asdf" \'fdsa\'') == "asdffdsa"
    assert interpret('b"asdf"') == b"asdf"
    assert interpret('b"asdf" b\'fdsa\'') == b"asdffdsa"
    with pytest.raises(SyntaxError):
        interpret('b"asdf" "fdsa"')
    with pytest.raises(SyntaxError):
        interpret('"asdf" b"fdsa"')
    # integer
    assert interpret('1') == 1
    assert interpret('1_000') == 1_000
    # floatnumber
    assert interpret('1.0') == 1.0
    assert interpret('1.') == 1.
    assert interpret('.1') == .1
    assert interpret('1e-3') == 1e-3
    # imagnumber
    assert interpret('1j') == 1j
    assert interpret('-1j') == -1j
    assert interpret('1 - 1j') == 1 - 1j
    assert interpret('1 + 1j') == 1 + 1j


# https://docs.python.org/3/reference/expressions.html#displays-for-lists-sets-and-dictionaries
def test_interpret_lists_sets_dicts_tuples(interpret):
    # lists
    # assert interpret('list()') == list()
    assert interpret('[]') == []
    assert interpret('[1, 2, 3]') == [1, 2, 3]
    # sets
    # assert interpret('set()') == set()
    assert interpret('{1, 2, 3, 3}') == {1, 2, 3, 3}
    # dicts
    # assert interpret('dict()') == dict()
    assert interpret('{}') == dict()
    assert interpret('{}') != set()
    assert interpret('{1: 11, 2: 22, 3: 33, 3: 44}') == {1: 11, 2: 22, 3: 33, 3: 44}
    # tuples
    # assert interpret('tuple()') == tuple()
    assert interpret('()') == ()
    assert interpret('(1)') != (1,)
    assert interpret('(1,)') == (1,)
    assert interpret('(1, 2, 3)') == (1, 2, 3)
    assert interpret('(1, 2, 3)') != [1, 2, 3]
    # combined
    assert interpret('([1, (2, 3)], {1, 2}, {1: 11, 2: 22})') == ([1, (2, 3)], {1, 2}, {1: 11, 2: 22})


def test_interpret_starred_lists_sets_dicts_tuples(interpret):
    # TODO: assert interpret('(1, *[2, 3], 4)') == (1, *[2, 3], 4)
    # TODO: assert interpret('[1, *(2, 3), 4]') == [1, *(2, 3), 4]
    # TODO: assert interpret('{**{1: 11, 3: 33}, **{2: 22, 3: 44}}') == {**{1: 11, 3: 33}, **{2: 22, 3: 44}}
    pass


# https://docs.python.org/3/library/stdtypes.html#boolean-operations-and-or-not
def test_interpret_boolean_operations(interpret):
    assert interpret('not True') == (not True)
    # test short circuit
    assert interpret('False or False or True') == (False or False or True)
    assert interpret('True and True and False') == (True and True and False)
    # test not short circuit
    assert interpret('False or False or False') == (False or False or False)
    assert interpret('True and True and True') == (True and True and True)


def test_interpret_binary_operators(interpret):
    assert interpret('9 + 2')  == 9 + 2
    assert interpret('9 - 2')  == 9 - 2
    assert interpret('9 * 2')  == 9 * 2
    # assert interpret('9 @ 2')  == 9 @ 2
    assert interpret('9 / 2')  == 9 / 2
    assert interpret('9 // 2') == 9 // 2
    assert interpret('9 % 2')  == 9 % 2
    assert interpret('9 ** 2') == 9 ** 2
    assert interpret('9 & 2')  == 9 & 2
    assert interpret('9 | 2')  == 9 | 2
    assert interpret('9 ^ 2')  == 9 ^ 2
    assert interpret('9 << 2') == 9 << 2
    assert interpret('9 >> 2') == 9 >> 2


def test_interpret_comparisons(interpret):
    assert interpret('9 < 2') == (9 < 2)
    assert interpret('9 <= 2') == (9 <= 2)
    assert interpret('9 > 2') == (9 > 2)
    assert interpret('9 >= 2') == (9 >= 2)
    assert interpret('9 == 2') == (9 == 2)
    assert interpret('9 != 2') == (9 != 2)
    assert interpret('None is None') == (None is None)
    assert interpret('None is not None') == (None is not None)


def test_interpret_comparisons_chained(interpret, interpret_nonstrict):
    with pytest.raises(DisabledLanguageFeatureError):
        interpret('1 <= 2 <= 4')
    assert interpret_nonstrict('1 <= 2 <= 4') == (1 <= 2 <= 4)
    assert interpret_nonstrict('1 <= 4 <= 2') == (1 <= 4 <= 2)


def test_interpret_unary_ops(interpret):
    # https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex
    assert interpret('+1') == +1
    assert interpret('-1') == -1
    assert interpret('+1j') == +1j
    assert interpret('-1j') == -1j
    # https://docs.python.org/3/library/stdtypes.html#boolean-operations-and-or-not
    assert interpret('not True') == (not True)
    # https://docs.python.org/3/library/stdtypes.html#bitwise-operations-on-integer-types
    assert interpret('~1') == ~1


# ========================================================================= #
# Interpreter                                                               #
# ========================================================================= #


def test_custom_interpreter(interpret):
    # make custom interpreter
    class CustomInterpreter(Interpreter):
        visit_Dict = None
    c_interpr = CustomInterpreter().interpret

    # specific feature disabled
    assert interpret('({1: 11}, 1)') == ({1: 11}, 1)
    with pytest.raises(DisabledLanguageFeatureError):
        assert c_interpr('({1: 11}, 1)')

    # something else still works
    assert interpret('({1, 2}, 1)') == ({1, 2}, 1)
    assert c_interpr('({1, 2}, 1)') == ({1, 2}, 1)


# TODO: these are not supported
# def test_interp_init_types(interpret):
#     assert interpret('list()') == list()
#     assert interpret('set()') == set()
#     assert interpret('dict()') == dict()
#     assert interpret('tuple()') == tuple()

# ========================================================================= #
# Original ast.literal_eval tests                                           #
# Relavent copyright applies for this section, I am not the owner.          #
# ========================================================================= #


def test_literal_eval(interpret, interpret_nonstrict):
    assert interpret('[1, 2, 3]') == [1, 2, 3]
    assert interpret('{"foo": 42}') == {"foo": 42}
    assert interpret('(True, False, None)') == (True, False, None)
    assert interpret('{1, 2, 3}') == {1, 2, 3}
    assert interpret('b"hi"') == b"hi"
    # assert interpret('set()') == set()
    assert interpret('6') == 6
    assert interpret('+6') == 6
    assert interpret('-6') == -6
    assert interpret('3.25') == 3.25
    assert interpret('+3.25') == 3.25
    assert interpret('-3.25') == -3.25
    assert repr(interpret('-0.0')) == '-0.0'
    # This is technically valid python... allow it
    with pytest.raises(DisabledLanguageFeatureError):
        assert interpret('++6') == 6
    assert interpret_nonstrict('++6') == 6
    # avoid SyntaxWarning on code coverage
    unary_true = +True
    with pytest.raises(DisabledLanguageFeatureError):
        assert interpret('+True') is unary_true
    assert interpret_nonstrict('+True') is unary_true
    # We want this...
    # with pytest.raises(UnsupportedLanguageFeatureError):
    assert interpret('2+3') == 5


def test_literal_eval_complex(interpret):
    # Issue #4907
    assert interpret('6j') == 6j
    assert interpret('-6j') == -6j
    assert interpret('6.75j') == 6.75j
    assert interpret('-6.75j') == -6.75j
    assert interpret('3+6j') == 3 + 6j
    assert interpret('-3+6j') == -3 + 6j
    assert interpret('3-6j') == 3 - 6j
    assert interpret('-3-6j') == -3 - 6j
    assert interpret('3.25+6.75j') == 3.25 + 6.75j
    assert interpret('-3.25+6.75j') == -3.25 + 6.75j
    assert interpret('3.25-6.75j') == 3.25 - 6.75j
    assert interpret('-3.25-6.75j') == -3.25 - 6.75j
    assert interpret('(3+6j)') == 3 + 6j
    # this is valid though... allow it
    # with pytest.raises(ValueError):
    interpret('-6j+3')
    # with pytest.raises(ValueError):
    interpret('-6j+3j')
    # with pytest.raises(ValueError):
    interpret('3+-6j')
    # with pytest.raises(ValueError):
    interpret('3+(0+6j)')
    # with pytest.raises(ValueError):
    interpret('-(3+6j)')


def test_literal_eval_malformed_dict_nodes(interpret):
    malformed = ast.Dict(keys=[ast.Constant(1), ast.Constant(2)], values=[ast.Constant(3)])
    with pytest.raises(ValueError):
        interpret(malformed)
    malformed = ast.Dict(keys=[ast.Constant(1)], values=[ast.Constant(2), ast.Constant(3)])
    with pytest.raises(ValueError):
        interpret(malformed)


def test_literal_eval_trailing_ws(interpret):
    assert interpret("    -1") == -1
    assert interpret("\t\t-1") == -1
    assert interpret(" \t -1") == -1
    with pytest.raises(IndentationError):
        interpret("\n -1")
    # extra
    assert interpret(" \t -1 \t ") == -1


def test_literal_eval_malformed_lineno(interpret, interpret_nonstrict):
    # but this stuff is valid... we want to allow it
    with pytest.raises(DisabledLanguageFeatureError, match=r'Nested unary operators are not allowed'):
        interpret("{'a': 1,\n'b':2,\n'c':++3,\n'd':4}")
    interpret_nonstrict("{'a': 1,\n'b':2,\n'c':++3,\n'd':4}")
    node = ast.UnaryOp(ast.UAdd(), ast.UnaryOp(ast.UAdd(), ast.Constant(6)))
    assert getattr(node, 'lineno', None) is None
    with pytest.raises(DisabledLanguageFeatureError, match=r'Nested unary operators are not allowed'):
        interpret(node)
    interpret_nonstrict(node)


# ========================================================================= #
# Original ast.literal_eval tests                                           #
# ========================================================================= #



class name:
    foo = 1
    class bar:
        baz = 2
    @staticmethod
    def taz(a=100, b=200):
        return 10 + a + b


conf = {'a': {'c': 1}, 'b': 2}


@pytest.fixture()
def name_sym_interp():
    interpret = Interpreter(
        default_symtable={'name': name, 'range': range, 'conf': conf},
        allow_unpacking=True,
    ).interpret
    return interpret


def test_interpreter_names(name_sym_interp):
    assert name_sym_interp('name') is name
    with pytest.raises(NameError):
        assert name_sym_interp('_unknown') is name.bar


def test_interpreter_properties(name_sym_interp):
    assert name_sym_interp('name.foo') is name.foo
    assert name_sym_interp('name.bar') is name.bar
    with pytest.raises(AttributeError):
        assert name_sym_interp('name._unknown') is name.bar

def test_interpreter_unpack(name_sym_interp):
    assert name_sym_interp('{*"abcaaaa"}') == {"a", "b", "c"} == {*"abcaaaa"}
    assert name_sym_interp('{*[1, 2], *(1, 2, 3)}') == {1, 2, 3}
    assert name_sym_interp('{1: 1.0, **{2: 2.0}, 3: 3.0}') == {1: 1.0, 2: 2.0, 3: 3.0}
    assert name_sym_interp('{1: 1.0, **{2: 2.0, **{4: 4.0}, **{4: 5.0}}, 3: 3.0}') == {1: 1.0, 2: 2.0, 3: 3.0, 4: 5.0}
    assert name_sym_interp('[1, *[2, *(3, 4), *{1, 2, 2}, 5], *{6: 6., 7: 7.}]') == [1, 2, 3, 4, 1, 2, 5, 6, 7]
    with pytest.raises(SyntaxError, match='invalid syntax'):
        assert name_sym_interp('[1, *[2, *(3, 4), *{1, 2, 2}, 5], **{6: 6., 7: 7.}]')

def test_interpreter_call(name_sym_interp):
    assert name_sym_interp('range(5)') == range(5)
    assert name_sym_interp('name.taz(1)') == name.taz(1)
    assert name_sym_interp('name.taz(a=1)') == name.taz(a=1)
    assert name_sym_interp('name.taz(b=2)') == name.taz(b=2)
    assert name_sym_interp('name.taz(a=1, b=2)') == name.taz(a=1, b=2)
    assert name_sym_interp('name.taz(1, b=2)') == name.taz(1, b=2)
    # technically this should raise SyntaxError, only TypeError for kwargs
    with pytest.raises(TypeError, match="got multiple values for keyword argument 'b'"):
        name_sym_interp('name.taz(b=1, b=2)')

def test_interpreter_call_and_unpack(name_sym_interp):
    # CALL TESTS
    assert name_sym_interp('[*range(5)]') == [0, 1, 2, 3, 4]

    # CALL & UNPACK TESTS
    assert name_sym_interp('name.taz(**{"b": 2})') == name.taz(**{"b": 2})
    assert name_sym_interp('name.taz(*[1], **{"b": 2})') == name.taz(*[1], **{"b": 2})
    assert name_sym_interp('name.taz(**{**{"b": 2}, **{"b": 3}})') == name.taz(b=3)
    with pytest.raises(TypeError, match="got multiple values for keyword argument 'a'"):
        name_sym_interp('name.taz(*[111], **{"a": 1}, **{"a": 11}, **{"b": 2})')


def test_interpreter_getitem(name_sym_interp):
    assert name_sym_interp('conf') is conf
    assert name_sym_interp('conf["a"]') == conf["a"]
    assert name_sym_interp('conf["b"]') == conf["b"]
    assert name_sym_interp('conf["a"]["c"]') == conf["a"]["c"]


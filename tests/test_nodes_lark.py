import pytest
from lark import UnexpectedToken, Tree, Token
from lark.visitors import Transformer

from eunomia.config.nodes._util_lark import SUB_PARSER, SUB_RECONSTRUCTOR


# ========================================================================= #
# Test Helper                                                               #
# ========================================================================= #


def parse(string) -> Tree:
    # TODO: this might actually be useful in the main code...

    # replace template_exp nodes by reconstructing
    # them for easier testing
    class ExprTransformer(Transformer):
        def template_exp(self, children):
            return ('exp', SUB_RECONSTRUCTOR.reconstruct(Tree('template_exp', children)))
        def template_ref(self, tokens):
            assert all(isinstance(tok, Token) for tok in tokens)
            return ('ref', '.'.join(str(tok) for tok in tokens) if tokens else None)
        def substitute_string(self, tokens):
            # this is a hack because of the grammer, just join
            # repetative chars together to form a string. so its easier to test.
            stack, str_stack = [], []
            for t in tokens:
                if isinstance(t, tuple):
                    if str_stack:
                        stack.append(''.join(str_stack))
                        str_stack.clear()
                    stack.append(t)
                else:
                    str_stack.append(t)
            if str_stack:
                stack.append(''.join(str_stack))
            return Tree('substitute_string', stack)

    # assert that the first node of the
    # tree is always 'substitute' and contains one child
    tree: Tree = SUB_PARSER.parse(string)
    assert tree.data == 'substitute'
    assert len(tree.children) == 1
    tree: Tree = tree.children[0]

    # assert that the second node of
    # the tree also only contains one child
    assert tree.data in {'substitute_string', 'interpret_fstring'}
    transformed = ExprTransformer().transform(tree)
    return transformed


# ========================================================================= #
# Test Grammar                                                              #
# ========================================================================= #


def test_lark_grammar():

    # helpers for testing parsed & transformed nodes
    def str(string):       return string
    def ref(string):       return ('ref', string)
    def exp(string):       return ('exp', string)

    def root_str(*args):   return Tree('substitute_string', list(args))
    def root_fstr(string): return Tree('interpret_fstring', [Token('FSTRING', string)])

    # parse strings
    assert parse('')                           == root_str()
    assert parse('asdf')                       == root_str(str('asdf'))
    assert parse('asdf   asdf')                == root_str(str('asdf   asdf'))
    assert parse('asdf   \t asdf')             == root_str(str('asdf   \t asdf'))
    assert parse('  \t asdf  \t  ')            == root_str(str('  \t asdf  \t  '))

    # basic reference
    assert parse('${a1.b2.c3}')  == root_str(ref('a1.b2.c3'))
    assert parse('${a1}')        == root_str(ref('a1'))
    with pytest.raises(UnexpectedToken):
        parse('${}')
    assert parse('     asdf   ${a}   ') == root_str(str('     asdf   '), ref('a'), str('   '))
    assert parse('\t    asdf   ${a}\t') == root_str(str('\t    asdf   '), ref('a'), str('\t'))

    # basic expr
    assert parse('${= 1+2}')              == root_str(exp('1+2'))
    assert parse('${=1 + 2}')             == root_str(exp('1+2'))
    assert parse('${=1 - 1}')             == root_str(exp('1-1'))
    with pytest.raises(UnexpectedToken):
        parse('${=}')

    # basic fstr
    assert parse('f"1+2+3"')              == root_fstr('f"1+2+3"')
    assert parse('f"1+2+{\'asdf\'}+3"')   == root_fstr('f"1+2+{\'asdf\'}+3"')
    assert parse("f'1+2+3={1+2+3}'")      == root_fstr("f'1+2+3={1+2+3}'")
    assert parse("f'1+2+3=${=1+2}'")      == root_fstr("f'1+2+3=${=1+2}'")

    # more complex combined
    assert parse('${a1}${=+1}${b2}')                  == root_str(ref('a1'), exp('+1'), ref('b2'))
    assert parse('asdf${a1}${=+1}${b2}')              == root_str(str('asdf'), ref('a1'), exp('+1'), ref('b2'))
    assert parse('asdf${a.b.c}fdaasd${a}${=1+2}')     == root_str(str('asdf'), ref('a.b.c'), str('fdaasd'), ref('a'), exp('1+2'))
    with pytest.raises(UnexpectedToken):
        parse('as df${a.b.c}fdaa\nsd${a}${{1+2}}')

    # these have a tendency to be buggy
    assert parse('${=[1]}')             == root_str(exp('[1]'))
    assert parse('${={1}}')             == root_str(exp('{1,}'))
    assert parse('${={ 1 }}')           == root_str(exp('{1,}'))
    assert parse('${={}}')              == root_str(exp('{}'))
    assert parse('${={1: 2}}')          == root_str(exp('{1:2,}'))
    assert parse('${={1, 2, 3}}')       == root_str(exp('{1,2,3,}'))
    assert parse('${={1,2}|{3,4}}')     == root_str(exp('{1,2,}|{3,4,}'))

    # test semi-colons
    with pytest.raises(UnexpectedToken): parse('${=;}')
    # disabled colons -- otherwise enable these
    with pytest.raises(UnexpectedToken): assert parse('${=1+2;}')            == root_str(exp('1+2'))
    with pytest.raises(UnexpectedToken): assert parse('as df${a.b.c}fdaa\tsd${a}${=1+2;}') == root_str(str('as df'), ref('a.b.c'), str('fdaa\tsd'), ref('a'), exp('1+2'))
    with pytest.raises(UnexpectedToken): assert parse('${=(1,);}')           == root_str(exp('(1,)'))
    with pytest.raises(UnexpectedToken): assert parse('${={1:2} ;}')         == root_str(exp('{1:2,}'))
    with pytest.raises(UnexpectedToken): assert parse('${= {1: 2} ;}')       == root_str(exp('{1:2,}'))
    with pytest.raises(UnexpectedToken): assert parse('${={};}')             == root_str(exp('{}'))
    with pytest.raises(UnexpectedToken): assert parse('f"asdf";')            == root_fstr('f"asdf"')

    # # check contained brackets
    assert parse('{}') == root_str(str('{}'))
    assert parse('a{}b') == root_str(str('a{}b'))
    assert parse('a{123}b') == root_str(str('a{123}b'))
    assert parse('a{123;}b') == root_str(str('a{123;}b'))
    assert parse('a{=123}b') == root_str(str('a{=123}b'))
    assert parse('a{=123;}b') == root_str(str('a{=123;}b'))
    assert parse('{=}') == root_str(str('{=}'))
    assert parse('{=1}') == root_str(str('{=1}'))
    assert parse('a{{}}b') == root_str(str('a{{}}b'))
    assert parse('a{{};}b') == root_str(str('a{{};}b'))
    assert parse('a{={}}b') == root_str(str('a{={}}b'))
    assert parse('a{={};}b') == root_str(str('a{={};}b'))

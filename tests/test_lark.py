import pytest
from lark import UnexpectedToken, Tree, Token
from lark.visitors import Transformer

from eunomia.nodes._util_lark import INTERPOLATE_PARSER, INTERPOLATE_RECONSTRUCTOR


# ========================================================================= #
# Test Helper                                                               #
# ========================================================================= #


def parse(string) -> Tree:
    # TODO: this might actaully be useful in the actual code...

    # replace template_exp nodes by reconstructing
    # them for easier testing
    class ExprTransformer(Transformer):
        def template_exp(self, children):
            return ('exp', INTERPOLATE_RECONSTRUCTOR.reconstruct(Tree('template_exp', children)))
        def template_ref(self, tokens):
            assert all(isinstance(tok, Token) for tok in tokens)
            return ('ref', '.'.join(str(tok) for tok in tokens) if tokens else None)
        def str(self, tokens):
            assert all(isinstance(tok, Token) for tok in tokens)
            assert len(tokens) == 1
            return ('str', str(tokens[0]))

    # assert that the first node of the
    # tree is always 'interpolate' and contains one child
    tree: Tree = INTERPOLATE_PARSER.parse(string)
    assert tree.data == 'interpolate'
    assert len(tree.children) == 1
    tree: Tree = tree.children[0]

    # assert that the second node of
    # the tree also only contains one child
    assert tree.data in {'interpolate_string', 'interpret_fstring'}
    return ExprTransformer().transform(tree)


# ========================================================================= #
# Test Grammar                                                              #
# ========================================================================= #


def test_lark_grammar():

    # helpers for testing parsed & transformed nodes
    def str(string):       return ('str', string)
    def ref(string):       return ('ref', string)
    def exp(string):       return ('exp', string)

    def root_str(*args):   return Tree('interpolate_string', list(args))
    def root_fstr(string): return Tree('interpret_fstring', [Token('FSTRING', string)])

    # parse strings
    assert parse('')                                  == root_str()
    assert parse('asdf')                              == root_str(str('asdf'))
    assert parse('asdf   asdf')                       == root_str(str('asdf   asdf'))
    assert parse('asdf   \t asdf')                    == root_str(str('asdf   \t asdf'))
    assert parse('  \t asdf  \t  ')                   == root_str(str('  \t asdf  \t  '))

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

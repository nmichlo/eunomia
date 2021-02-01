import pytest
from lark import UnexpectedToken, Tree, Token

from eunomia.nodes._util_lark import INTERPOLATE_PARSER


def test_lark_grammar():

    def interp(string):
        tokens = INTERPOLATE_PARSER.parse(string)
        print('- '*100)
        print(string)
        print(tokens)
        return tokens

    # TODO: str should match fstr
    def exp(*args): return Tree('template_exp', list(args))
    def str(string): return Tree('str', [Token('STR', string)])
    def ref(*names): return Tree('template_ref', [Token('NAME', n) for n in names])
    def root_str(*args): return Tree('interpolate', [Tree('interpolate_string', list(args))])
    def root_fstr(string): return Tree('interpolate', [Tree('interpret_fstring', [Token('FSTRING', string)])])

    expr_1_minus_1 = exp(Tree('arith_expr', [Tree('number', [Token('DEC_NUMBER', '1')]), Token('MINUS', '-'), Tree('number', [Token('DEC_NUMBER', '1')])]))
    expr_1_plus_2 = exp(Tree('arith_expr', [Tree('number', [Token('DEC_NUMBER', '1')]), Token('PLUS', '+'), Tree('number', [Token('DEC_NUMBER', '2')])]))
    expr_plus_1 = exp(Tree('factor', [Token('PLUS', '+'), Tree('number', [Token('DEC_NUMBER', '1')])]))

    assert interp('')     == root_str()
    assert interp('asdf') == root_str(str('asdf'))
    assert interp('asdf${a.b.c}fdaasd${a}${{1+2}}')    == root_str(str('asdf'), ref('a', 'b', 'c'), str('fdaasd'), ref('a'), expr_1_plus_2)
    assert interp('as df${a.b.c}fdaa\tsd${a}${{1+2}}') == root_str(str('as df'), ref('a', 'b', 'c'), str('fdaa\tsd'), ref('a'), expr_1_plus_2)

    with pytest.raises(UnexpectedToken):
        interp('as df${a.b.c}fdaa\nsd${a}${{1+2}}')

    assert interp('${a1.b2.c3}')           == root_str(ref('a1', 'b2', 'c3'))
    assert interp('${a1}${{+1}}${b2}')     == root_str(ref('a1'), expr_plus_1, ref('b2'))
    assert interp('asdf${a1}${{+1}}${b2}') == root_str(str('asdf'), ref('a1'), expr_plus_1, ref('b2'))
    assert interp('${{1 + 2}}')            == root_str(expr_1_plus_2)
    assert interp('${{1 - 1}}')            == root_str(expr_1_minus_1)
    assert interp('${{f"a{1}b{1-1}c"}}')   == root_str(Tree('template_exp', [Tree('string', [Token('STRING', 'f"a{1}b{1-1}c"')])]))
    assert interp('f"1+2+3"')              == root_fstr('f"1+2+3"')
    assert interp("f'1+2+3={1+2+3}'")      == root_fstr("f'1+2+3={1+2+3}'")

    assert interp('${{[1]}}')            == root_str(exp( Tree('list', [Tree('number', [Token('DEC_NUMBER', '1')])]) ))
    assert interp('${{{1} }}')           == root_str(exp( Tree('set', [Tree('set_comp', [Tree('number', [Token('DEC_NUMBER', '1')])])]) ))
    assert interp('${{(1,)}}')           == root_str(exp( Tree('tuple', [Tree('tuplelist_comp', [Tree('number', [Token('DEC_NUMBER', '1')])])]) ))
    assert interp('${{{1:2} }}')         == root_str(exp( Tree('dict', [Tree('dict_comp', [Tree('key_value', [Tree('number', [Token('DEC_NUMBER', '1')]), Tree('number', [Token('DEC_NUMBER', '2')])])])]) ))
    assert interp('${{ {1:2} }}')        == root_str(exp( Tree('dict', [Tree('dict_comp', [Tree('key_value', [Tree('number', [Token('DEC_NUMBER', '1')]), Tree('number', [Token('DEC_NUMBER', '2')])])])]) ))
    assert interp('${{{}}}')             == root_str(exp( Tree('dict', []) ))

    # TODO: these are bugs that need to be fixed...
    with pytest.raises(UnexpectedToken): interp('${{{1:2}}}')
    with pytest.raises(UnexpectedToken): interp('${{ {1:2}}}')
    with pytest.raises(UnexpectedToken): interp('${{{1}}}')
    with pytest.raises(UnexpectedToken): interp('${{ {1}}}')

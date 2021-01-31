# from functools import partial
#
# import pytest
# from eunomia._DEPRICATED._interpolation import _tokenize_string, TOKEN_STRING, TOKEN_INTERP, TokenizeError
#
#
# def test_parse():
#
#     tokenize = partial(_tokenize_string, bgn_tok='${', end_tok='}$')
#
#     assert tokenize('ac') == ([(TOKEN_STRING, 'ac')], False)
#     assert tokenize('${b}$') == ([(TOKEN_INTERP, 'b')], True)
#     assert tokenize('${}$') == ([(TOKEN_INTERP, '')], True)
#     assert tokenize('${b}$c') == ([(TOKEN_INTERP, 'b'), (TOKEN_STRING, 'c')], True)
#     assert tokenize('a${b}$') == ([(TOKEN_STRING, 'a'), (TOKEN_INTERP, 'b')], True)
#     assert tokenize('a${b}$c') == ([(TOKEN_STRING, 'a'), (TOKEN_INTERP, 'b'), (TOKEN_STRING, 'c')], True)
#     assert tokenize('prefix${interp}$suffix') == ([(TOKEN_STRING, 'prefix'), (TOKEN_INTERP, 'interp'), (TOKEN_STRING, 'suffix')], True)
#     assert tokenize('a${b}$c${d}$e') == ([(TOKEN_STRING, 'a'), (TOKEN_INTERP, 'b'), (TOKEN_STRING, 'c'), (TOKEN_INTERP, 'd'), (TOKEN_STRING, 'e')], True)
#     assert tokenize('a${b}$${d}$e') == ([(TOKEN_STRING, 'a'), (TOKEN_INTERP, 'b'), (TOKEN_INTERP, 'd'), (TOKEN_STRING, 'e')], True)
#     assert tokenize('a${}$${}$e') == ([(TOKEN_STRING, 'a'), (TOKEN_INTERP, ''), (TOKEN_INTERP, ''), (TOKEN_STRING, 'e')], True)
#
#     with pytest.raises(TokenizeError):
#         tokenize('prefix${interp}suffix')
#
#     string = 'prefix{interp}$suffix'
#     tokenize(string, strict_end=False)
#     with pytest.raises(TokenizeError):
#         tokenize(string, strict_end=True)
#
#     with pytest.raises(TokenizeError):
#         assert tokenize('prefix${int${erp}$suffix') == 1



# interp_str('')
# interp_str('asdf')
# interp_str('asdf${a.b.c}fdaasd${a}${{1+2}}')
# interp_str('as df${a.b.c}fdaa\tsd${a}${{1+2}}')
# interp_str('as df${a.b.c}fdaansd${a}${{1+2}}')
# interp_str('${a1.b2.c3}')
# interp_str('${a1}${{+1}}${b2}')
# interp_str('asdf${a1}${{+1}}${b2}')
# interp_str('${{1 + 2}}')
# interp_str('${{f"a{1}b{1+1}c"}}')
# interp_str('f"1+2+3"')
# interp_str("f'1+2+3={1+2+3}'")
#
#
# # parse('fdsa')
# # parse('asdf${f1.f2.f3}$')
# # parse('asdf${f1.f2.f3}$fdsa')
# # parse('asdf${eval:f1.f2.f3}$fdsa${eval:f1.f2.f3}$')
# # parse('asdf${}$fdsa')
# # parse('asdf${fdsa}$fdsa')
# # parse('${eval:"asdf"}$')
# # parse('${eval:set(c.asdf.fdsa)}$')
# # parse('${eval:[1,2,3,4]}$')
# # parse('${eval:  lambda: 3}$')
# # parse('asdffds')
# # parse(' ad ${asdf}$')
# # parse(' ad ${asdf}$ fda')
# # parse('${asdf}$ fda')




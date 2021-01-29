from functools import partial

import pytest
from eunomia._DEPRICATED._interpolation import _tokenize_string, TOKEN_STRING, TOKEN_INTERP, TokenizeError


def test_parse():

    tokenize = partial(_tokenize_string, bgn_tok='${', end_tok='}$')

    assert tokenize('ac') == ([(TOKEN_STRING, 'ac')], False)
    assert tokenize('${b}$') == ([(TOKEN_INTERP, 'b')], True)
    assert tokenize('${}$') == ([(TOKEN_INTERP, '')], True)
    assert tokenize('${b}$c') == ([(TOKEN_INTERP, 'b'), (TOKEN_STRING, 'c')], True)
    assert tokenize('a${b}$') == ([(TOKEN_STRING, 'a'), (TOKEN_INTERP, 'b')], True)
    assert tokenize('a${b}$c') == ([(TOKEN_STRING, 'a'), (TOKEN_INTERP, 'b'), (TOKEN_STRING, 'c')], True)
    assert tokenize('prefix${interp}$suffix') == ([(TOKEN_STRING, 'prefix'), (TOKEN_INTERP, 'interp'), (TOKEN_STRING, 'suffix')], True)
    assert tokenize('a${b}$c${d}$e') == ([(TOKEN_STRING, 'a'), (TOKEN_INTERP, 'b'), (TOKEN_STRING, 'c'), (TOKEN_INTERP, 'd'), (TOKEN_STRING, 'e')], True)
    assert tokenize('a${b}$${d}$e') == ([(TOKEN_STRING, 'a'), (TOKEN_INTERP, 'b'), (TOKEN_INTERP, 'd'), (TOKEN_STRING, 'e')], True)
    assert tokenize('a${}$${}$e') == ([(TOKEN_STRING, 'a'), (TOKEN_INTERP, ''), (TOKEN_INTERP, ''), (TOKEN_STRING, 'e')], True)

    with pytest.raises(TokenizeError):
        tokenize('prefix${interp}suffix')

    string = 'prefix{interp}$suffix'
    tokenize(string, strict_end=False)
    with pytest.raises(TokenizeError):
        tokenize(string, strict_end=True)

    with pytest.raises(TokenizeError):
        assert tokenize('prefix${int${erp}$suffix') == 1

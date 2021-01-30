from lark.reconstruct import Reconstructor
from lark.visitors import Interpreter


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def _read_relative_file(path):
    import pathlib
    dir = pathlib.Path(__file__).parent.absolute().joinpath(path)
    with open(dir, 'r') as f:
        return f.read()


def _get_lark_interpolate_parser():
    from lark import Lark
    grammar = _read_relative_file(GRAMMAR_FILE)
    return Lark(grammar, parser='lalr')


GRAMMAR_FILE = 'interpolate.lark'
INTERPOLATE_PARSER = _get_lark_interpolate_parser()
INTERPOLATE_RECONSTRUCTOR = Reconstructor(INTERPOLATE_PARSER)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

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



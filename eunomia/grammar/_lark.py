

# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #
from eunomia._interpreter import interpret_expr


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
PARSER = _get_lark_interpolate_parser()


# ========================================================================= #
# Helper Functions                                                          #
# ========================================================================= #


def _interpolate_string(node, usersyms=None):
    assert node.data == 'interpolate_string'
    strings = []
    for token in node.children:
        if token.data == 'template_ref':
            strings.append('<@>')
        elif token.data == 'template_exp':
            strings.append('<!>')
        elif token.data == 'str':
            assert len(token.children) == 1
            strings.append(str(token.children[0]))
        else:
            raise RuntimeError(f'Unknown token encountered: {token}')
    # if the expression is the only value in the string,
    # then return the actual value instead.
    if len(strings) == 1:
        return strings[0]
    else:
        return ''.join(str(v) for v in strings)


def _interpret_fstring(node, usersyms=None):
    assert node.data == 'interpret_fstring'
    assert len(node.children) == 1
    expr = str(node.children[0])
    return interpret_expr(expr, usersyms=usersyms)


def interpolate_string(string, usersyms=None):
    tree = PARSER.parse(string)

    assert tree.data == 'interpolate'
    assert len(tree.children) == 1
    node = tree.children[0]

    if node.data == 'interpolate_string':
        return _interpolate_string(node, usersyms=usersyms)
    elif node.data == 'interpret_fstring':
        return _interpret_fstring(node, usersyms=usersyms)
    else:
        raise RuntimeError('This should never happen!')



# ========================================================================= #
# End                                                                       #
# ========================================================================= #

def interp_str(string):
    string = interpolate_string(string)
    print('\033[92m', string, '\033[0m')


interp_str('')
interp_str('asdf')
interp_str('asdf${a.b.c}fdaasd${a}${{1+2}}')
interp_str('as df${a.b.c}fdaa\tsd${a}${{1+2}}')
interp_str('as df${a.b.c}fdaansd${a}${{1+2}}')
interp_str('${a1.b2.c3}')
interp_str('${a1}${{+1}}${b2}')
interp_str('asdf${a1}${{+1}}${b2}')
interp_str('${{1 + 2}}')
interp_str('${{f"a{1}b{1+1}c"}}')
interp_str('f"1+2+3"')
interp_str("f'1+2+3={1+2+3}'")


# parse('fdsa')
# parse('asdf${f1.f2.f3}$')
# parse('asdf${f1.f2.f3}$fdsa')
# parse('asdf${eval:f1.f2.f3}$fdsa${eval:f1.f2.f3}$')
# parse('asdf${}$fdsa')
# parse('asdf${fdsa}$fdsa')
# parse('${eval:"asdf"}$')
# parse('${eval:set(c.asdf.fdsa)}$')
# parse('${eval:[1,2,3,4]}$')
# parse('${eval:  lambda: 3}$')
# parse('asdffds')
# parse(' ad ${asdf}$')
# parse(' ad ${asdf}$ fda')
# parse('${asdf}$ fda')



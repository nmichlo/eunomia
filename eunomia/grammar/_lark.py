

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
PARSER = _get_lark_interpolate_parser()


# ========================================================================= #
# Helper Functions                                                          #
# ========================================================================= #


def _interpolate_string(node):
    assert node.data == 'interpolate_string'

def _interpret_fstring(node):
    assert node.data == 'interpret_fstring'


def interpolate_string(string):
    tree = PARSER.parse(string)

    assert tree.data == 'interpolate'
    assert len(tree.children) == 1
    node = tree.children[0]

    if node.data == 'interpolate_string':
        strings = []
        return ''.join(strings)
    elif node.data == 'interpret_fstring':
        pass
    else:
        raise RuntimeError('This should never happen!')



    print(tree.pretty())
    print()


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


interpolate_string('')
interpolate_string('asdf')
interpolate_string('asdf${a.b.c}fdaasd${a}${{1+2}}')
interpolate_string('${a1.b2.c3}')
interpolate_string('${a1}${{+1}}${b2}')
interpolate_string('asdf${a1}${{+1}}${b2}')
interpolate_string('${{1 + 2}}')
interpolate_string('${{f"a{1}b{1+1}c"}}')
interpolate_string('f"1+2+3"')
interpolate_string("f'1+2+3'")


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




from lark import Lark

def load_grammar(name):
    import pathlib
    dir = pathlib.Path(__file__).parent.absolute().joinpath('grammar', name + '.lark')
    with open(dir, 'r') as f:
        return f.read()

# ========================================================================= #
# Printing                                                                  #
# ========================================================================= #


def parse(string):
    print("="*100)
    print('\033[92m', string, '\033[0m')
    try:
        result = PARSER.parse(string)
        print(result)
        print(result.pretty())
    except Exception as e:
        print('\033[91m', e, '\033[0m')
    print("="*100)


PARSER = Lark(load_grammar('interp_v1'))


parse('')
parse('${}')
parse('${asdf}$')
parse('fdsa')
parse('asdf${f1.f2.f3}$')
parse('asdf${f1.f2.f3}$fdsa')
parse('asdf${eval:f1.f2.f3}$fdsa${eval:f1.f2.f3}$')
parse('asdf${}$fdsa')
parse('asdf${fdsa}$fdsa')
parse('${eval:"asdf"}$')
parse('${eval:set(c.asdf.fdsa)}$')
parse('${eval:[1,2,3,4]}$')
parse('${eval:  lambda: 3}$')
parse('asdffds')
parse(' ad ${asdf}$')
parse(' ad ${asdf}$ fda')
parse('${asdf}$ fda')



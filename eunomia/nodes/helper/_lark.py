from lark.reconstruct import Reconstructor


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


GRAMMAR_FILE = 'grammar_interpolate.lark'
INTERPOLATE_PARSER = _get_lark_interpolate_parser()
INTERPOLATE_RECONSTRUCTOR = Reconstructor(INTERPOLATE_PARSER)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


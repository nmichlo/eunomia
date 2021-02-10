from lark.reconstruct import Reconstructor


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def _read_relative_file(path):
    import pathlib
    dir = pathlib.Path(__file__).parent.absolute().joinpath(path)
    with open(dir, 'r') as f:
        return f.read()


def _get_lark_substitute_parser():
    from lark import Lark
    grammar = _read_relative_file(GRAMMAR_FILE)
    return Lark(grammar, parser='lalr')


GRAMMAR_FILE = 'grammar_substitute.lark'
SUB_PARSER = _get_lark_substitute_parser()
SUB_RECONSTRUCTOR = Reconstructor(SUB_PARSER)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


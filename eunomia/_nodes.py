

# ========================================================================= #
# Yaml Loader                                                               #
# ========================================================================= #


class Node(object):
    TAG = None

    def __init__(self, value: str):
        assert isinstance(value, str), f'{value=} corresponding to {self.TAG} must be a string.'
        self.raw_value = value

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.raw_value)})'

    def __str__(self):
        return f'{self.TAG} {repr(self.raw_value)}'

    def get(self):
        raise NotImplementedError


class RefNode(Node):
    TAG = '!ref'

    def get(self):
        return self.raw_value


class EvalNode(Node):
    TAG = '!eval'

    def get(self):
        return self.make_interpreter().eval(self.raw_value, show_errors=False)

    def make_interpreter(self):
        import asteval
        return asteval.Interpreter(
            # symtable=None, usersyms=None, writer=None, err_writer=None, use_numpy=True, minimal=False,
            no_if=True, no_for=True, no_while=True, no_try=True, no_functiondef=True,
            # no_ifexp=False, no_listcomp=False,
            no_augassign=True, no_assert=True, no_delete=True, no_raise=True, no_print=True,
            # max_time=None, readonly_symbols=None,
            builtins_readonly=True,
        )


class InterpNode(Node):

    def __init__(self, value: str):
        assert isinstance(value, list), f'{value=} must be a list parsed by _tokenize_string'
        self.raw_value = value

    def get(self):
        # TODO!
        raise NotImplementedError


# ========================================================================= #
# Yaml Loader                                                               #
# ========================================================================= #

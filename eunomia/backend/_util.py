

# ========================================================================= #
# Object Traversal                                                          #
# ========================================================================= #


class ContainerTransformer(object):

    """
    Based off of the various transformers that
    exist for traversing ASTs.

    This one effectively makes copies of the
    containers being traversed.
    """

    def __init__(self, visit_keys=True):
        self.visit_keys = visit_keys

    def visit(self, value):
        attr = f'_visit_{type(value).__name__}'
        func = getattr(self, attr)
        return func(value)

    def __getattr__(self, name):
        return self.__default__

    def __default__(self, value):
        return value

    def _visit_set(self, value):
        return set(self.visit(v) for v in value)

    def _visit_list(self, value):
        return list(self.visit(v) for v in value)

    def _visit_tuple(self, value):
        return tuple(self.visit(v) for v in value)

    def _visit_dict(self, value):
        if self.visit_keys:
            return dict((self.visit(k), self.visit(v)) for k, v in value.items())
        return dict((k, self.visit(v)) for k, v in value.items())


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

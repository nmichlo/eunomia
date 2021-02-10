

# ========================================================================= #
# Object Traversal                                                          #
# ========================================================================= #


class Transformer(object):
    """
    Based off of the various transformers that
    exist for traversing ASTs.

    This one effectively makes copies of the
    containers being traversed.
    """

    def transform(self, value):
        attr = f'_transform_{type(value).__name__}'
        func = getattr(self, attr, self.__transform_default__)
        return func(value)

    def __transform_default__(self, value):
        raise NotImplementedError


class Visitor(object):
    """
    Based off of the various visitors that
    exist for traversing ASTs.
    """

    def visit(self, value):
        attr = f'_visit_{type(value).__name__}'
        func = getattr(self, attr, self.__visit_default__)
        func(value)

    def __visit_default__(self, value):
        raise NotImplementedError


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

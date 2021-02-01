

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

    def visit(self, value):
        attr = f'_visit_{type(value).__name__}'
        func = getattr(self, attr, self.__default__)
        return func(value)

    def __default__(self, value):
        raise NotImplementedError

    def _visit_set(self, value): return set(self.visit(v) for v in value)
    def _visit_list(self, value): return list(self.visit(v) for v in value)
    def _visit_tuple(self, value): return tuple(self.visit(v) for v in value)
    def _visit_dict(self, value): return {self._visit_dict_key(k): self._visit_dict_value(v) for k, v in value.items()}

    def _visit_dict_key(self, key): return self.visit(key)
    def _visit_dict_value(self, value): return self.visit(value)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

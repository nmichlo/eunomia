

# ========================================================================= #
# Object Traversal                                                          #
# ========================================================================= #


class PyTransformer(object):

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

    def _transform_set(self, value):
        return set(self.transform(v) for v in value)

    def _transform_list(self, value):
        return list(self.transform(v) for v in value)

    def _transform_tuple(self, value):
        return tuple(self.transform(v) for v in value)

    def _transform_dict(self, value):
        return {self._transform_dict_key(k): self._transform_dict_value(v) for k, v in value.items()}

    def _transform_dict_key(self, key):
        return self.transform(key)

    def _transform_dict_value(self, value):
        return self.transform(value)


class PyVisitor(object):

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

    def _visit_set(self, value):
        for v in value:
            self.visit(v)

    def _visit_list(self, value):
        for v in value:
            self.visit(v)

    def _visit_tuple(self, value):
        for v in value:
            self.visit(v)

    def _visit_dict(self, value):
        for k, v in value.items():
            self._visit_dict_key(k)
            self._visit_dict_value(v)

    def _visit_dict_key(self, key):
        self.visit(key)

    def _visit_dict_value(self, value):
        self.visit(value)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

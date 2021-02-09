from schema import SchemaError
from eunomia.config.scheme import VerboseGroup


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class Backend(object):

    def load_root_group(self):
        root = self._load_root_group()
        try:
            return VerboseGroup.validate(root)
        except SchemaError as e:
            raise ValueError(f'Loaded schema is invalid for backend: {self.__class__.__name__}.\n{e}')

    def _load_root_group(self):
        raise NotImplementedError


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

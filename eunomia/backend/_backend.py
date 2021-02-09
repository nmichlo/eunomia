from schema import SchemaError
from eunomia.config.objects import Group
from eunomia.config.scheme import VerboseGroup


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class Backend(object):

    def load_root_group(self) -> Group:
        root = self._load_root_group()
        try:
            root.to_dict()
        except SchemaError as e:
            raise ValueError(f'Invalid loaded config for backend: {self.__class__.__name__}.\n{e}')
        return root

    def _load_root_group(self) -> Group:
        raise NotImplementedError


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

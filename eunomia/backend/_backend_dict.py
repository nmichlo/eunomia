from eunomia.backend import Backend
from eunomia.config import Group


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class BackendDict(Backend):

    def __init__(self, root_dict: dict):
        if not isinstance(root_dict, dict):
            raise TypeError(f'root_dict must be a dict')
        self._root_dict = root_dict

    def _load_root_group(self):
        return Group.from_dict(self._root_dict)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


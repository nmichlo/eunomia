from eunomia.backend._backend import Backend
from eunomia.config.objects import Group


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class BackendDict(Backend):

    def __init__(self, root_dict: dict, mode='verbose'):
        # check the root folder
        if not isinstance(root_dict, dict):
            raise TypeError(f'root_dict must be a dict')
        self._root_dict = root_dict
        self._from_fn = {
            'verbose': Group.from_dict,
            'compact': Group.from_compact_dict,
        }[mode]

    def _load_root_group(self):
        return self._from_fn(self._root_dict)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


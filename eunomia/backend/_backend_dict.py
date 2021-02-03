"""
The "Internal" Backend is the data structures
used by the core config loader. For checking and merging.

The backend effectively passes through the values as they
are without any modifications.
"""


from eunomia.config import ConfigGroup
from eunomia.backend._backend import Backend


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class BackendDict(Backend):

    def __init__(self, root_dict: dict):
        # check the root folder
        if not isinstance(root_dict, dict):
            raise TypeError(f'root_dict must be a dict')
        self._root_dict = root_dict        # loading modes

    def load_root_group(self) -> ConfigGroup:
        # use _group_ tag to differentiate
        # between groups and options
        raise NotImplementedError('TODO: implement me')


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


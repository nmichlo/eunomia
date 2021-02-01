"""
The "Internal" Backend is the data structures
used by the core config loader. For checking and merging.

The backend effectively passes through the values as they
are without any modifications.
"""

from eunomia.backend._backend import Backend
from eunomia.backend._config_objects import ConfigGroup


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class BackendInternal(Backend):

    def __init__(self, root_group: ConfigGroup):
        if not isinstance(root_group, ConfigGroup):
            raise TypeError(f'{root_group} must be an instance of {ConfigGroup.__name__}')
        self._root_group = root_group

    def _load_root_group(self) -> ConfigGroup:
        return self._root_group


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


from eunomia.backend import Backend
from eunomia.config import Group


# ========================================================================= #
# Internal Backend                                                          #
# ========================================================================= #


class BackendObj(Backend):
    """
    The most basic backend is the ConfigObject data structures
    used by the core config loader.

    The backend passes through the values as they
    are without any modifications.
    """

    def __init__(self, root_group: Group):
        if not isinstance(root_group, Group):
            raise TypeError(f'root_group must be an instance of {Group.__name__}')
        self._root_group = root_group

    def _load_root_group(self) -> Group:
        return self._root_group


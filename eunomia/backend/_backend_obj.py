from eunomia.backend import Backend
from eunomia.config import Group, Option


# ========================================================================= #
# Object Backend                                                            #
# ========================================================================= #


class BackendObj(Backend):
    """
    The most basic backend is the ConfigObject data structures
    used by the core config loader.

    The backend passes through the values as they
    are without any modifications.
    """

    GROUP_TYPE = Group
    OPTION_TYPE = Option

    def _load_group(cls, value) -> Group:
        return value  # pragma: no cover

    def _load_option(cls, value) -> Option:
        return value  # pragma: no cover

    def _dump_group(self, group: Group):
        return group  # pragma: no cover

    def _dump_option(self, option: Option):
        return option  # pragma: no cover


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

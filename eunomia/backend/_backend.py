from eunomia.backend._config_objects import ConfigGroup


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class Backend(object):

    def load_root_group(self) -> ConfigGroup:
        raise NotImplementedError


# ========================================================================= #
# Internal Backend                                                          #
# ========================================================================= #


class BackendConfigGroup(Backend):
    """
    The most basic backend is the ConfigObject data structures
    used by the core config loader.

    The backend passes through the values as they
    are without any modifications.
    """

    def __init__(self, root_group: ConfigGroup):
        if not isinstance(root_group, ConfigGroup):
            raise TypeError(f'{root_group} must be an instance of {ConfigGroup.__name__}')
        self._root_group = root_group

    def load_root_group(self) -> ConfigGroup:
        return self._root_group


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

from eunomia.config import Group as Group


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class Backend(object):

    def load_root_group(self) -> Group:
        return self._load_root_group()

    def _load_root_group(self) -> Group:
        raise NotImplementedError


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

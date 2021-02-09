"""
The "Internal" Backend is the data structures
used by the core config loader. For checking and merging.

The backend effectively passes through the values as they
are without any modifications.
"""


from eunomia.backend._backend import Backend
import eunomia.config.scheme as s


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class BackendDict(Backend):
    """
    The most basic backend!
    Just passes through the raw dictionary.
    """

    def __init__(self, root_dict: dict):
        # check the root folder
        if not isinstance(root_dict, dict):
            raise TypeError(f'root_dict must be a dict')
        # try validate everything, we don't use the result but want the errors now
        s.VerboseGroup.validate(root_dict)
        self._root_dict = root_dict

    def _load_root_group(self):
        return self._root_dict


# ========================================================================= #
# Compact Dictionary Backend                                                #
# ========================================================================= #


class BackendCompactDict(Backend):
    """
    The most basic backend!
    Just passes through the raw dictionary.
    """

    def __init__(self, root_dict: dict):
        # check the root folder
        if not isinstance(root_dict, dict):
            raise TypeError(f'root_dict must be a dict')
        # try validate everything, we don't use the result but want the errors now
        s.CompactGroup.validate(root_dict)
        self._root_dict = root_dict

    def _load_root_group(self):
        # TODO: convert from VerboseGroup to CompactGroup
        raise NotImplementedError('TODO: convert from VerboseGroup to CompactGroup')


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


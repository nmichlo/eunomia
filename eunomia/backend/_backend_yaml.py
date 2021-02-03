"""
The "Internal" Backend is the data structures
used by the core config loader. For checking and merging.

The backend effectively passes through the values as they
are without any modifications.
"""

from glob import glob
import os

from eunomia.config import ConfigGroup, ConfigOption
from eunomia.backend._backend import Backend
from eunomia.backend._util_yaml import yaml_load_file


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class BackendYaml(Backend):

    def __init__(self, root_folder: str):
        # check the root folder
        if not isinstance(root_folder, str):
            raise TypeError(f'{root_folder=} must be a string')
        if not os.path.isdir(root_folder):
            raise FileNotFoundError(f'{root_folder=} is not a valid directory.\n\tAre you sure the path is correct and not relative?\n\tCurrent working directory is: {repr(os.getcwdb().decode())}')
        self._root_folder = root_folder        # loading modes

    def load_root_group(self) -> ConfigGroup:
        ext = '.yaml'
        # get all yaml files
        paths = glob(os.path.join(self._root_folder, f'**/*{ext}'), recursive=True)
        # remove root folder from names
        paths = [os.path.relpath(path, self._root_folder) for path in paths]
        # sort paths by length, then alphabetically
        paths = sorted(paths, key=lambda p: (len(s := p.split('/')), *s))
        # traverse group and add
        root = ConfigGroup()
        for path in paths:
            # strip yaml extension & split path into group
            assert path.endswith(ext)
            (*subgroups, option_name) = split_valid_value_path(path[:-len(ext)])
            # add subgroups
            group = root.get_subgroups_recursive(subgroups, make_missing=True)
            # add option by loading file
            data = yaml_load_file(os.path.join(self._root_folder, path))
            group.add_option(option_name, ConfigOption(data))
        # done!
        return root


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


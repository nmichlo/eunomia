"""
The "Internal" Backend is the data structures
used by the core config loader. For checking and merging.

The backend effectively passes through the values as they
are without any modifications.

We use the hydra-config terminology:
https://hydra.cc/docs/terminology/

- (Config) Group:
    A mutually exclusive set of (Config Group) Options. These groups
    can be hierarchical such that standard path notation is used.
    (eg. group/subgroup/subsubgroup)

- (Config Group) Option:
    One of the selectable configs in a (Config) Group.

- (Config Option) Node:
    A Config Node is either a Value Node (a primitive type), or a Container
    Node. A Container Node is a list or dictionary of Value Nodes.

- Package:
    A Package is the path of the Config Node in the Config Object.

"""


from typing import Union
from eunomia._keys import assert_valid_eunomia_key, split_eunomia_path, KEY_OPTIONS, KEY_PACKAGE, PACKAGE_DEFAULT


# ========================================================================= #
# Group                                                                     #
# ========================================================================= #


class Group(object):

    def __init__(self):
        super().__init__()
        self._groups = {}
        self._options = {}

    @property
    def groups(self):
        return dict(self._groups)

    @property
    def options(self):
        return dict(self._options)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Checks                                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _check_get(self, key: str):
        # asserting that it is a valid path to a group or config
        # we only allow groups or configs to be inserted at a depth of 1.
        keys = split_eunomia_path(key)
        if len(keys) != 1:
            raise ValueError(f'Group key must only have one level: {repr(key)}')

    def _check_insert(self, key: str):
        self._check_get(key)
        # TODO: maybe relax limitation that groups and options should have different names?
        if key in self._groups: raise KeyError(f'Group already has subgroup: {repr(key)}')
        if key in self._options: raise KeyError(f'Group already has option: {repr(key)}')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Getters, Setters                                                      #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def __setitem__(self, key: str, value: Union['Group', 'Option']):
        self._check_insert(key)
        if isinstance(value, Option):
            self._options[key] = value
        elif isinstance(value, Group):
            self._groups[key] = value
        else:
            raise TypeError
        return value

    def __getitem__(self, key: str):
        self._check_get(key)
        if key in self._options:
            return self._options[key]
        elif key in self._groups:
            return self._groups[key]
        raise KeyError

    def __getattr__(self, key: str):
        try:
            return self.__getitem__(key)
        except KeyError:
            return self.__getattribute__(key)

    def __setattr__(self, key: str, value: Union['Group', 'Option']):
        if isinstance(value, (Group, Option)):
            self.__setitem__(key, value)
        else:
            # TODO: this could cause errors if not disabled.
            super().__setattr__(key, value)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Getters, Setters                                                      #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    get = __getitem__
    set = __setitem__

    def get_subgroup(self, key) -> 'Group':
        self._check_get(key)
        return self._groups[key]

    def get_option(self, key) -> 'Option':
        self._check_get(key)
        return self._options[key]

    def new_subgroup(self, key) -> 'Group':
        return self.set_subgroup(key, Group())

    def new_option(self, key) -> 'Option':
        return self.set_option(key, Option())

    def set_subgroup(self, key: str, value: 'Group') -> 'Group':
        assert isinstance(value, Group)
        return self.set(key, value)

    def set_option(self, key: str, value: 'Option') -> 'Option':
        assert isinstance(value, Option)
        return self.set(key, value)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Conversion                                                            #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @classmethod
    def from_dict(cls, dct: dict):
        # TODO: implement me
        raise NotImplementedError


# ========================================================================= #
# Option                                                                    #
# ========================================================================= #


class Option(object):

    def __init__(self, dct: dict, path: list[str]):
        self.path = path
        # extract various components from the config
        self.defaults = self._config_pop_options(dct)
        self.package = self._config_pop_package(dct)
        self.dct = dct

    def _config_pop_options(self, data: dict) -> dict:
        defaults = data.pop(KEY_OPTIONS, {})
        assert isinstance(defaults, dict), f'Config: {self.path=} ERROR: defaults must be a mapping!'
        # check that the chosen options are valid!
        for k, v in defaults.items():
            assert_valid_eunomia_key(k)
            if not isinstance(v, str):
                raise TypeError(f'Config: {self.path=} values in chosen options must be strings.')
        return defaults

    def _config_pop_package(self, data: dict) -> str:
        package = data.pop(KEY_PACKAGE, PACKAGE_DEFAULT)
        assert isinstance(package, str), f'Config: {self.path=} ERROR: package must be a string!'
        return package


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


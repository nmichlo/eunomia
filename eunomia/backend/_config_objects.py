"""

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
from eunomia._keys import KEY_OPTIONS, KEY_PACKAGE, KEY_PLUGINS, KEYS_RESERVED_ALL, assert_valid_single_option_key
from eunomia._keys import PKG_DEFAULT_ALIAS
from eunomia._keys import assert_valid_value_package, assert_valid_value_path, assert_valid_single_key
from eunomia._keys import join_valid_value_path, join_valid_value_package
from eunomia.backend._util import ContainerVisitor


# ========================================================================= #
# Config Node                                                               #
# ========================================================================= #


class _ConfigObject(object):

    def __init__(self):
        super().__init__()
        self._parent = None
        self._key = None
        self._children = {}

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Path                                                                  #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @property
    def has_parent(self):
        return self._key or self._parent

    @property
    def path(self):
        if not self.has_parent:
            return None
        return join_valid_value_path(*(n.key for n in self._walk_from_root(visit_self=True, visit_root=False)))

    @property
    def package(self):
        if not self.has_parent:
            return None
        return join_valid_value_package(*(n.key for n in self._walk_from_root(visit_self=True, visit_root=False)))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Walk                                                                  #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _walk_to_root(self, visit_self=True, visit_root=False):
        current = self
        if visit_self:
            yield current
        while current.parent is not None:
            current = current.parent
            if current.parent is not None:
                yield current
        if visit_root:
            yield current

    def _walk_from_root(self, visit_self=True, visit_root=False):
        yield from reversed(list(self._walk_to_root(
            visit_self=visit_self,
            visit_root=visit_root
        )))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Children                                                              #
    # - for simplicity we do not allow attribute access to children.        #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def add_child(self, key: str, child: '_ConfigObject') -> '_ConfigObject':
        assert_valid_single_key(key)
        # check the child node
        if not isinstance(child, _ConfigObject):
            raise TypeError(f'child must be an instance of {_ConfigObject.__name__}')
        if child._parent or child._key:
            raise ValueError(f'child has already has a parent, and cannot be added.')
        if (not child._parent) ^ (not child._key):
            raise ValueError('child node is malformed. Has a key or a parent, but not both.')
        # check the parent node
        if key in self._children:
            raise KeyError(f'parent already has child with key: {key}')
        # set details
        child._parent = self
        child._key = key
        self._children[key] = child
        # return the added value
        return child

    def get_child(self, key) -> Union['_ConfigObject']:
        return self._children[key]

    __setitem__ = add_child
    __getitem__ = get_child

    def __iter__(self):
        yield from self._children


# ========================================================================= #
# Group                                                                     #
# ========================================================================= #


class ConfigGroup(_ConfigObject):

    def __init__(self, option_or_group_nodes: dict[str, Union['ConfigGroup', 'ConfigOption']] = None):
        super().__init__()
        # add groups or options
        if option_or_group_nodes:
            for k, v in option_or_group_nodes.items():
                self.add_child(k, v)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Override                                                              #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def add_child(self, key: str, node: Union['ConfigGroup', 'ConfigOption']) -> Union['ConfigGroup', 'ConfigOption']:
        # additional key checks - can only be one deep "group" not "group/subgroup" etc.
        assert_valid_value_path([key])
        # check node types
        if not isinstance(node, (ConfigGroup, ConfigOption)):
            raise TypeError(f'Can only add {ConfigGroup.__name__} and {ConfigOption.__name__} nodes to {ConfigGroup.__name__}')
        # add!
        assert super().add_child(key, node) is node
        # we dont return the above because of type warnings
        return node

    # override to yield in order
    def __iter__(self):
        yield from (k for k, v in self._children if isinstance(v, ConfigGroup))
        yield from (k for k, v in self._children if isinstance(v, ConfigOption))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Getters                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @property
    def groups(self) -> dict[str, 'ConfigGroup']:
        return {k: v for k, v in self._children if isinstance(v, ConfigGroup)}

    @property
    def options(self) -> dict[str, 'ConfigOption']:
        return {k: v for k, v in self._children if isinstance(v, ConfigOption)}

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Groups & Options                                                      #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def get_subgroup(self, key: str) -> 'ConfigGroup':
        node = self.get_child(key)
        if isinstance(node, ConfigGroup):
            raise TypeError(f'node with key: {key} is not a {ConfigGroup.__name__}')
        return node

    def get_option(self, key: str) -> 'ConfigOption':
        node = self.get_child(key)
        if isinstance(node, ConfigOption):
            raise TypeError(f'node with key: {key} is not a {ConfigOption.__name__}')
        return node

    def add_subgroup(self, key: str, value: 'ConfigGroup') -> 'ConfigGroup':
        assert isinstance(value, ConfigGroup)
        return self.add_child(key, value)

    def add_option(self, key: str, value: 'ConfigOption') -> 'ConfigOption':
        assert isinstance(value, ConfigOption)
        return self.add_child(key, value)

    def new_subgroup(self, key: str) -> 'ConfigGroup':
        return self.add_subgroup(key, ConfigGroup())

    # we don't support new_option because we shouldn't
    # modify it after it is initialised
    # def new_option(self, key: str) -> 'ConfigOption':
    #     return self.add_option(key, ConfigOption())

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Strings                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'{self.__class__.__name__}({self._children})'


# ========================================================================= #
# Option                                                                    #
# ========================================================================= #


class ConfigOption(_ConfigObject):

    def __init__(self, raw_config: dict):
        super().__init__()
        self._raw_config = raw_config
        # TODO: checks -- this needs to be cleaned up!
        self.raw_config

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # getters                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @property
    def options(self) -> dict:
        options = self._raw_config.get(KEY_OPTIONS, {})
        self._check_option_keys_and_values(options)
        return dict(options)

    @property
    def package(self) -> str:
        package = self._raw_config.get(KEY_PACKAGE, PKG_DEFAULT_ALIAS)
        self._check_package_values(package)
        return str(package)

    @property
    def plugins(self) -> dict:
        plugins = self._raw_config.get(KEY_PLUGINS, {})
        self._check_plugins(plugins)
        return dict(plugins)

    @property
    def config(self) -> dict:
        raw = dict(self._raw_config)
        for key in KEYS_RESERVED_ALL:
            if key in raw:
                del raw[key]
        return raw

    @property
    def raw_config(self) -> dict:
        raw = dict(self._raw_config)
        self._check_raw_config(raw)
        # TODO: checks -- this needs to be cleaned up!
        self.options
        self.package
        self.plugins
        return raw

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Checks                                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _check_option_keys_and_values(self, options: dict):
        assert isinstance(options, dict), f'{ConfigOption.__name__}: {repr(self.path)} ERROR: value for {KEY_OPTIONS} must be a mapping!'
        # check that the chosen options are valid!
        # options can only be one item deep
        for k, v in options.items():
            assert_valid_value_path([k])
            assert_valid_value_path([v])

    def _check_package_values(self, package: str):
        assert isinstance(package, str), f'{ConfigOption.__name__}: {repr(self.path)} ERROR: value for {KEY_PACKAGE} must be a string!'
        # check that the package is valid
        assert_valid_value_package(package)

    def _check_plugins(self, plugins: dict):
        assert isinstance(plugins, dict), f'{ConfigOption.__name__}: {repr(self.path)} ERROR: value for {KEY_PLUGINS} must be a mapping!'
        # TODO: more checks?

    class _RawOptionConfigKeyChecker(ContainerVisitor):
        def __default__(self, value):
            print(value)
            pass
        def _visit_dict_key(self, key):
            print(key)
            assert_valid_single_option_key(key)

    _check_raw_config = _RawOptionConfigKeyChecker().visit

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Children - disabled for the option node                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    add_child   = None
    get_child   = None
    __setitem__ = None
    __getitem__ = None
    __iter__    = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Strings                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'{self.__class__.__name__}({self._raw_config})'


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

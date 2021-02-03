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


from typing import Union, Optional, Sequence
from eunomia.config.keys import KEY_OPTIONS, KEY_PACKAGE, KEY_PLUGINS, KEYS_RESERVED_ALL
from eunomia.config.keys import Key, GroupKey, Path, GroupPath, PkgPath
from eunomia._util_traverse import PyVisitor
from eunomia.values import BaseValue


# ========================================================================= #
# Config Node                                                               #
# ========================================================================= #


class _ConfigObject(object):

    KeyType = Key
    PathType = Path
    KeyTypeHint = Union[str, KeyType]

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
        assert not ((not self._key) ^ (not self._parent))
        return self._key and self._parent

    @property
    def parent(self) -> '_ConfigObject':
        assert self.has_parent
        return self._parent

    @property
    def key(self) -> KeyType:
        assert self.has_parent
        return self._key

    @property
    def path(self) -> PathType:
        return self.PathType([n.key for n in self._walk_from_root(visit_root=False)])

    @property
    def root(self) -> '_ConfigObject':
        node = self
        for node in self._walk_to_root(visit_root=True):
            pass
        return node

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Walk                                                                  #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _walk_to_root(self, visit_root=False):
        current = self
        while current.has_parent:
            yield current
            current = current.parent
        if visit_root:
            yield current

    def _walk_from_root(self, visit_root=False):
        yield from reversed(list(self._walk_to_root(
            visit_root=visit_root
        )))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Children                                                              #
    # - for simplicity we do not allow attribute access to children.        #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def add_child(self, key: KeyTypeHint, child: '_ConfigObject') -> '_ConfigObject':
        key = self.KeyType(key)
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

    def get_child(self, key: KeyTypeHint) -> Union['_ConfigObject']:
        key = self.KeyType(key)
        return self._children[key]

    def has_child(self, key: KeyTypeHint) -> bool:
        key = self.KeyType(key)
        return key in self._children

    __setitem__ = add_child
    __getitem__ = get_child
    __contains__ = has_child

    def __iter__(self):
        yield from self._children


# ========================================================================= #
# Group                                                                     #
# ========================================================================= #


class ConfigGroup(_ConfigObject):

    KeyType = GroupKey
    PathType = GroupPath
    KeyTypeHint = Union[str, KeyType]
    PathTypeHint = Union[str, Sequence[Union[str, KeyType]], PathType]
    NodeTypeHint = Union['ConfigGroup', 'ConfigOption']

    def __init__(self, option_or_group_nodes: dict[str, NodeTypeHint] = None):
        super().__init__()
        # add groups or options
        if option_or_group_nodes:
            for k, v in option_or_group_nodes.items():
                child = self.add_child(k, v)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Override                                                              #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def add_child(self, key: KeyTypeHint, node: NodeTypeHint) -> NodeTypeHint:
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

    def get_subgroup(self, key: KeyTypeHint) -> 'ConfigGroup':
        node = self.get_child(key)
        if not isinstance(node, ConfigGroup):
            raise TypeError(f'node with key: {repr(key)} is not a {ConfigGroup.__name__}')
        return node

    def get_option(self, key: KeyTypeHint) -> 'ConfigOption':
        node = self.get_child(key)
        if not isinstance(node, ConfigOption):
            raise TypeError(f'node with key: {repr(key)} is not a {ConfigOption.__name__}')
        return node

    def add_subgroup(self, key: KeyTypeHint, value: 'ConfigGroup') -> 'ConfigGroup':
        if not isinstance(value, ConfigGroup):
            raise TypeError(f'adding node with key: {repr(key)} is not a {ConfigGroup.__name__}')
        return self.add_child(key, value)

    def add_option(self, key: KeyTypeHint, value: 'ConfigOption') -> 'ConfigOption':
        if not isinstance(value, ConfigOption):
            raise TypeError(f'adding node with key: {repr(key)} is not a {ConfigOption.__name__}')
        return self.add_child(key, value)

    def new_subgroup(self, key: KeyTypeHint) -> 'ConfigGroup':
        return self.add_subgroup(key, ConfigGroup())

    def get_subgroups_recursive(self, path: PathTypeHint, make_missing=False) -> 'ConfigGroup':
        keys = self.PathType(path).keys
        def _recurse(group, old_keys):
            if not old_keys:
                return group
            key, keys = old_keys[0], old_keys[1:]
            if make_missing:
                if not group.has_subgroup(key):
                    return _recurse(group.new_subgroup(key), keys)
            return _recurse(group.get_subgroup(key), keys)
        return _recurse(self, keys)

    def has_subgroup(self, key: KeyTypeHint):
        key = self.KeyType(key)
        return (key in self._children) and isinstance(self._children[key], ConfigGroup)

    def has_option(self, key: KeyTypeHint):
        key = self.KeyType(key)
        return (key in self._children) and isinstance(self._children[key], ConfigOption)

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

    KeyType = GroupKey
    PathType = GroupPath
    KeyTypeHint = Union[str, KeyType]

    def __init__(self, raw_config: dict):
        super().__init__()
        self._raw_config = raw_config

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # getters                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @property
    def group(self) -> ConfigGroup:
        assert self.has_parent
        g = self.parent
        assert isinstance(g, ConfigGroup)
        return g

    @property
    def group_path(self) -> GroupPath:
        return GroupPath(self.group.path)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # getters                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def resolve_package(self, merged_config, merged_options, current_config) -> PkgPath:
        package = self._raw_config.get(KEY_PACKAGE, PkgPath.PKG_DEFAULT_ALIAS)
        if isinstance(package, BaseValue):
            package = package.get_config_value(merged_config, merged_options, current_config)
        return PkgPath.try_from_alias(package, self)

    @property
    def options(self) -> dict:
        options = self._raw_config.setdefault(KEY_OPTIONS, {})
        # self._check_option_keys_and_values(options)
        return options

    @property
    def plugins(self) -> Optional[dict]:
        plugins = self._raw_config.setdefault(KEY_PLUGINS, {})
        # self._check_plugins(plugins)
        return plugins

    @property
    def config(self) -> dict:
        raw = dict(self._raw_config)
        for key in KEYS_RESERVED_ALL:
            if key in raw:
                del raw[key]
        return raw

    # @property
    # def raw_config(self) -> dict:
    #     raw = dict(self._raw_config)
    #     # self._check_raw_config(raw)
    #     return raw

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Checks                                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _check_option_keys_and_values(self, options: dict):
        assert isinstance(options, dict), f'{ConfigOption.__name__}: {repr(self.path)} ERROR: value for {repr(KEY_OPTIONS)} must be a mapping!'
        # check that the chosen options are valid!
        # options can only be one item deep
        for k, v in options.items():
            assert_valid_value_path([k])
            assert_valid_value_path([v])

    def _check_package_values(self, package: str):
        assert isinstance(package, str), f'{ConfigOption.__name__}: {repr(self.path)} ERROR: value for {repr(KEY_PACKAGE)} must be a string!'
        # check that the package is valid
        assert_valid_value_package(package)

    def _check_plugins(self, plugins: dict):
        assert isinstance(plugins, dict), f'{ConfigOption.__name__}: {repr(self.path)} ERROR: value for {repr(KEY_PLUGINS)} must be a mapping!'
        # TODO: more checks?

    class _RawOptionConfigKeyChecker(PyVisitor):
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

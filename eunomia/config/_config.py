from typing import Dict, Union, List, Tuple

from eunomia._util_traverse import RecursiveTransformer
from eunomia.config.nodes import ConfigNode, SubNode

from eunomia.config import keys as K
from eunomia.config import validate as V


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
    def _is_valid_parent(self):
        return not ((not self._key) ^ (not self._parent))

    @property
    def has_parent(self):
        assert self._is_valid_parent
        return (self._key is not None) and (self._parent is not None)

    @property
    def parent(self) -> '_ConfigObject':
        assert self._is_valid_parent
        return self._parent

    @property
    def key(self) -> str:
        assert self._is_valid_parent
        return self._key

    @property
    def keys(self) -> Tuple[str]:
        return tuple(n.key for n in self.walk_from_root(visit_root=False))

    @property
    def abs_path(self):
        return '/' + '/'.join(self.keys if self.keys else ())

    @property
    def root(self) -> '_ConfigObject':
        node = self
        for node in self.walk_to_root(visit_root=True):
            pass
        return node

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Walk                                                                  #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def walk_to_root(self, visit_root=False):
        current = self
        while current.has_parent:
            yield current
            current = current.parent
        if visit_root:
            yield current

    def walk_from_root(self, visit_root=False):
        yield from reversed(list(self.walk_to_root(
            visit_root=visit_root
        )))

    def walk_descendants(self):
        def _iter(node):
            yield node
            for k in node:
                yield from _iter(node[k])
        return _iter(self)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Children                                                              #
    # - for simplicity we do not allow attribute access to children.        #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def add_child(self, key: str, child: '_ConfigObject') -> '_ConfigObject':
        if not isinstance(child, _ConfigObject):
            raise TypeError(f'child must be an instance of {_ConfigObject.__name__}')
        if child.has_parent:
            raise ValueError(f'child already has a parent, and cannot be added.')
        if key in self._children:
            raise KeyError(f'parent already has child with key: {key}')
        # set details
        child._parent = self
        child._key = key
        self._children[key] = child
        # return the added value
        return child

    def del_child(self, key: str):
        child = self.get_child(key)
        # remove details
        child._parent = None
        child._key = None
        del self._children[key]

    def get_child(self, key: str):
        return self._children[key]

    def has_child(self, key: str):
        return key in self._children

    __setitem__ = add_child
    __getitem__ = get_child
    __contains__ = has_child

    def __iter__(self):
        yield from self._children


# ========================================================================= #
# Group                                                                     #
# ========================================================================= #


class Group(_ConfigObject):

    def __init__(
            self,
            named_nodes: Dict[str, Union['Group', 'Option']] = None,
    ):
        super().__init__()
        # add groups or options
        if named_nodes:
            for k, v in named_nodes.items():
                self.add_child(k, v)
            # we dont need to validate groups because we dont
            # directly support conversion to them yet.

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Override                                                              #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def add_child(self, key, node: Union['Group', 'Option']) -> Union['Group', 'Option']:
        if not isinstance(node, (Group, Option)):
            raise TypeError(f'Can only add {Group.__name__} and {Option.__name__} nodes to {Group.__name__}')
        # add!
        assert super().add_child(key, node) is node
        # we dont return the above because of type warnings
        return node

    # override to yield in order
    def __iter__(self):
        yield from self.groups
        yield from self.options

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Getters                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @property
    def root(self) -> 'Group':
        g = super().root
        assert isinstance(g, Group)
        return g

    @property
    def groups(self) -> Dict[str, 'Group']:
        return {k: v for k, v in self._children.items() if isinstance(v, Group)}

    @property
    def options(self) -> Dict[str, 'Option']:
        return {k: v for k, v in self._children.items() if isinstance(v, Option)}

    @property
    def group_keys(self) -> Tuple[str]:
        return self.keys

    @property
    def abs_group_path(self):
        return self.abs_path

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Groups & Options                                                      #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def get_subgroup(self, key: str) -> 'Group':
        node = self.get_child(key)
        if not isinstance(node, Group):
            raise TypeError(f'node with key: {repr(key)} is not a {Group.__name__}')
        return node

    def del_subgroup(self, key: str) -> 'Option':
        assert self.has_subgroup(key)
        self.del_child(key)

    def get_option(self, key: str) -> 'Option':
        node = self.get_child(key)
        if not isinstance(node, Option):
            raise TypeError(f'node with key: {repr(key)} is not a {Option.__name__}')
        return node

    def add_subgroup(self, key: str, value: 'Group') -> 'Group':
        if not isinstance(value, Group):
            raise TypeError(f'adding node with key: {repr(key)} is not a {Group.__name__}')
        return self.add_child(key, value)

    def add_option(self, key: str, value: 'Option') -> 'Option':
        if not isinstance(value, Option):
            raise TypeError(f'adding node with key: {repr(key)} is not a {Option.__name__}')
        return self.add_child(key, value)

    def del_option(self, key: str) -> 'Option':
        assert self.has_suboption(key)
        self.del_child(key)

    def new_subgroup(self, key: str) -> 'Group':
        return self.add_subgroup(key, Group())

    def new_option(self, key: str, data=None, pkg=None, defaults=None) -> 'Option':
        return self.add_option(key, Option(
            data=data, pkg=pkg, defaults=defaults
        ))

    def has_suboption(self, key):
        if not self.has_child(key):
            return False
        if not isinstance(self.get_child(key), Option):
            return False
        return True

    def has_subgroup(self, key):
        if not self.has_child(key):
            return False
        if not isinstance(self.get_child(key), Group):
            return False
        return True

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Walk                                                                  #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def get_subgroup_recursive(self, keys: List[str], make_missing=False) -> 'Group':
        def _recurse(group: Group, old_keys):
            if not old_keys:
                return group
            key, keys = old_keys[0], old_keys[1:]
            if make_missing:
                if not group.has_subgroup(key):
                    return _recurse(group.new_subgroup(key), keys)
            return _recurse(group.get_subgroup(key), keys)
        return _recurse(self, keys)

    def get_group_from_path(self, path: str, make_missing=False):
        """
        This function checks if a path is relative or absolute.
        If the path is relative, it traverses from the current group.
        If the path is absolute, it traverses from the root group.

        Supports make_missing like get_subgroups_recursive(...)
        """
        group_keys, is_relative = V.split_config_path(path)
        # get the group corresponding to the path - must handle relative & root paths
        root = (self if is_relative else self.root)
        return root.get_subgroup_recursive(group_keys, make_missing=make_missing)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Strings                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'{self.__class__.__name__}({self._children})'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Debug                                                                 #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def debug_tree_print(
            self, colors=True, show_options=True, full_option_path=True,
            full_group_path=True, show_defaults=False
    ):
        from eunomia.config._config_debug import debug_tree_print
        debug_tree_print(
            self, colors=colors, show_options=show_options, full_option_path=full_option_path,
            full_group_path=full_group_path, show_defaults=show_defaults
        )


# ========================================================================= #
# Option                                                                    #
# ========================================================================= #


class Option(_ConfigObject):

    def __init__(
            self,
            data: dict = None,
            pkg: str = None,
            defaults: list = None,
    ):
        super().__init__()
        # extract components
        self._data = V.validate_option_data(data)
        self._pkg = V.validate_option_package(pkg)
        self._defaults = V.validate_option_defaults(defaults, allow_config_nodes=True)

    @property
    def pkg(self):
        return self._pkg

    @property
    def data(self):
        return self._data.copy()

    @property
    def defaults(self):
        return self._defaults.copy()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # getters                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @property
    def root(self) -> 'Group':
        assert self.has_parent
        g = super().root
        assert isinstance(g, Group)
        return g

    @property
    def group(self) -> Group:
        assert self.has_parent
        g = self.parent
        assert isinstance(g, Group)
        return g

    @property
    def group_keys(self) -> Tuple[str]:
        return self.group.keys

    @property
    def abs_group_path(self):
        return self.group.abs_group_path

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # getters - data                                                        #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    class _ReplaceStrings(RecursiveTransformer):
        def _transform_str(self, value):
            return SubNode(value)
        def __transform_default__(self, value):
            return value
        def _transform_dict_key(self, key):
            # do not allow interpolation on keys
            if isinstance(key, str):
                return key
            elif isinstance(key, ConfigNode):
                raise TypeError(f'keys in configs cannot be config nodes: {key}')
            return super()._transform_dict_key(key)

    def get_unresolved_defaults(self):
        return self._ReplaceStrings().transform(self._defaults)

    def get_unresolved_package(self):
        return self._ReplaceStrings().transform(self._pkg)

    def get_unresolved_data(self):
        return self._ReplaceStrings().transform(self._data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Children - disabled for the option node                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    add_child = None
    get_child = None
    __setitem__ = None
    __getitem__ = None
    __iter__ = ().__iter__

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Strings                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'{self.__class__.__name__}(data={repr(self._data)}, pkg={repr(self._pkg)}, defaults={repr(self._defaults)})'


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

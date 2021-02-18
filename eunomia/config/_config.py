from typing import Dict, Union, List, Tuple

from eunomia.util._util_traverse import RecursiveTransformer
from eunomia.config.nodes import ConfigNode, SubNode

from eunomia.config import validate as V
from eunomia.config import keys as K


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

    def get_package_keys(self, pkg_override: str = None) -> Tuple[str]:
        raise NotImplementedError

    @property
    def group(self) -> 'Group':
        raise NotImplementedError

    @property
    def abs_path(self):
        return V.keys_as_abs_config_path(self.keys)

    @property
    def root(self) -> '_ConfigObject':
        node = self
        for node in self.walk_to_root(visit_root=True):
            pass
        return node

    def rel_keys_to(self, right: '_ConfigObject'):
        if right.root is not self.root:
            raise AssertionError('trying to get relative path to config object in different tree.')
        # check that we are a parent
        l_keys, r_keys = self.keys, right.keys
        while l_keys:
            if not r_keys:
                raise KeyError('left config object is a child of the right config object')
            (l_key, *l_keys), (r_key, *r_keys) = l_keys, r_keys
            if l_key != r_key:
                raise KeyError('left config object is not a parent of the right config object')
        return r_keys

    def rel_path_to(self, right: '_ConfigObject'):
        return '/'.join(self.rel_keys_to(right))

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
        return child

    def get_child(self, key: str):
        return self._children[key]

    def has_child(self, key: str):
        return key in self._children

    __setitem__ = add_child
    __getitem__ = get_child
    __contains__ = has_child

    def __iter__(self):
        raise NotImplementedError


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

    def walk_descendant_options(self):
        for node in self.walk_descendants():
            if isinstance(node, Option):
                yield node

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Getters                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @property
    def root(self) -> 'Group':
        g = super().root
        assert isinstance(g, Group)
        return g

    @property
    def group(self) -> 'Group':
        return self

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
    # Package                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def get_package_keys(self, pkg_override=None) -> Tuple[str]:
        assert pkg_override is None, 'cannot override the groups package'
        return self.keys

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Groups & Options                                                      #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def get_subgroup(self, key: str) -> 'Group':
        node = self.get_child(key)
        if not isinstance(node, Group):
            raise TypeError(f'node with key: {repr(key)} is not a {Group.__name__}')
        return node

    def del_subgroup(self, key: str) -> 'Group':
        assert self.has_subgroup(key)
        return self.del_child(key)

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
        return self.del_child(key)

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

    def _get_keys_and_root(self, path: Union[str, List[str], Tuple[str]]):
        if isinstance(path, str):
            group_keys, is_relative = V.split_config_path(path)
            # get the group corresponding to the path - must handle relative & root paths
            root = (self if is_relative else self.root)
        else:
            group_keys, root = path, self
        return group_keys, root

    def get_child_recursive(self, path: Union[str, List[str], Tuple[str]], make_missing_as_groups=False) -> Union['Group', 'Option']:
        keys, current = self._get_keys_and_root(path)
        while keys:
            (key, *keys) = keys
            if isinstance(current, Option):
                raise KeyError(f'an option has no descendants, tired to visit child {repr(key)} of option {repr(current.abs_path)}')
            if not current.has_child(key):
                if not make_missing_as_groups:
                    raise KeyError(f'{current.__class__.__name__} {repr(current.abs_path)} does not have child {repr(key)}')
                else:
                    if not isinstance(current, Group):
                        raise KeyError(f'cannot make missing group {repr(key)} on option {repr(current.abs_path)} for path {repr(path)}')
                    current.new_subgroup(key)
            current = current.get_child(key)
        return current

    def get_group_recursive(self, path: Union[str, List[str], Tuple[str]], make_missing=False) -> 'Group':
        """
        This function checks if a path is relative or absolute.
        If the path is relative, it traverses from the current group.
        If the path is absolute, it traverses from the root group.

        NOTE: If the path is a *list* of keys,
              they are considered *relative*.

        Supports make_missing, to create any missing groups.
        """
        group = self.get_child_recursive(path, make_missing_as_groups=make_missing)
        if not isinstance(group, Group):
            raise KeyError(f'{group.__class__.__name__} config object at path {repr(path)} is not a group.')
        return group

    def get_option_recursive(self, path: Union[str, List[str], Tuple[str]]) -> 'Option':
        """
        This function is like get_group_recursive, checking for relative
        and absolute paths, except the last component of the path should
        be an option name.

        NOTE: If the path is a *list* of keys,
              they are considered *relative*.
        """
        (*group_keys, option_name), root = self._get_keys_and_root(path)
        group = self.get_group_recursive(group_keys, make_missing=False)
        if not group.has_suboption(option_name):
            raise KeyError(f'group {repr(group.abs_group_path)} does not have suboption {repr(option_name)}')
        return group.get_option(option_name)

    def has_group_recursive(self, path: Union[str, List[str], Tuple[str]]):
        try:
            self.get_group_recursive(path, make_missing=False)
            return True
        except KeyError:
            return False

    def has_option_recursive(self, path: Union[str, List[str], Tuple[str]]):
        try:
            self.get_option_recursive(path)
            return True
        except KeyError:
            return False

    def path_to_abs_keys(self, path: Union[str, List[str], Tuple[str]]) -> Tuple[str]:
        """
        convert a relative or abs path to abs keys
        """
        path, root = self._get_keys_and_root(path)
        return root.keys + tuple(path)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Strings                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'{self.__class__.__name__}({self._children})'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Merge                                                                 #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def absorb_children(self, group: 'Group', allow_replace_options=False) -> 'Group':
        # like dict.update, but modify right hand side...
        if not isinstance(group, Group):
            raise TypeError('group can only absorb other groups.')
        # -- this should be split out into a func
        if group.root is self.root:
            raise AssertionError('tried to absorb group from the same tree.')
        # recursive walk to check conflicts first, so that things arent modified if there is a failure
        # TODO: this is not very efficient, walks down tree each time to check...
        # -- this should maybe be split out into a func
        if not allow_replace_options:
            for r_option in group.walk_descendant_options():
                r_rel_keys = group.rel_keys_to(r_option)
                if self.has_option_recursive(r_rel_keys):
                    l_option = self.get_option_recursive(r_rel_keys)
                    raise KeyError(f'left group {repr(self.abs_path)} cannot absorb right group {repr(group.abs_path)} because conflicting left option was found at {repr(l_option.abs_path)} and right option at {repr(r_option.abs_path)}.')
        # do absorb!
        self._absorb_children(group, allow_replace_options=allow_replace_options)
        return self

    def _absorb_children(self, group: 'Group', allow_replace_options: bool):
        # absorb options
        for r_option_name, r_option in group.options.items():
            group.del_option(r_option_name)
            # remove left option if allowed
            if self.has_suboption(r_option_name):
                if allow_replace_options:
                    self.del_option(r_option_name)
                else:
                    raise AssertionError('This is a bug and should never happen! Check that no conflicts exist first!')
            # add right option to left
            self.add_option(r_option_name, r_option)
        # absorb subgroups
        for r_group_name, r_group in group.groups.items():
            group.del_subgroup(r_group_name)
            if self.has_subgroup(r_group_name):
                # recursively absorb if same group already exists in left
                self.get_subgroup(r_group_name)._absorb_children(r_group, allow_replace_options=allow_replace_options)
            else:
                # add right group to left
                self.add_subgroup(r_group_name, r_group)

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
    def pkg(self) -> str:
        return self._pkg

    @property
    def data(self) -> dict:
        return self._data.copy()

    @property
    def defaults(self) -> list:
        return self._defaults

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
    def abs_group_path(self) -> str:
        return self.group.abs_group_path

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Package                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def get_package_keys(self, pkg_override: str = None) -> Tuple[str]:
        pkg = self._pkg if (pkg_override is None) else pkg_override
        # resolve special keys
        if pkg in K.ALL_PACKAGE_ALIASES:
            if pkg == K.PKG_ROOT: return tuple()
            elif pkg == K.PKG_GROUP: return self.group_keys
            elif pkg == K.PKG_OPTION: return self.keys
            else: raise AssertionError('it is a bug and should never happen.')
        # split
        keys, is_relative = V.split_package_path(pkg)
        # resolve relative -- NOTE! RELATIVE from the GROUP not the option
        if is_relative:
            keys = self.group_keys + keys
        return keys

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

    def get_unresolved_defaults(self) -> List['Default']:
        from eunomia.config._default import Default
        return [Default(d) for d in self._defaults]

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

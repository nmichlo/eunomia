from typing import Dict, Union, List, Tuple

from eunomia._util_traverse import RecursiveTransformer
from eunomia.config import scheme as s
from eunomia.config.nodes import ConfigNode, SubNode


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
        assert not ((not self._key) ^ (not self._parent))
        return (self._key is not None) and (self._parent is not None)

    @property
    def parent(self) -> '_ConfigObject':
        assert self.has_parent
        return self._parent

    @property
    def key(self) -> str:
        assert self.has_parent
        return self._key

    @property
    def keys(self) -> Tuple[str]:
        return tuple(n.key for n in self.walk_from_root(visit_root=False))

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

    def get_child(self, key: str):
        return self._children[key]

    def has_child(self, key: str):
        return key in self._children

    __setitem__ = add_child
    __getitem__ = get_child
    __contains__ = has_child

    def __iter__(self):
        yield from self._children

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Schema                                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @classmethod
    def from_dict(cls, mapping: dict, validate=True):
        raise NotImplementedError

    def to_dict(self, validate=True):
        raise NotImplementedError

    def is_valid_dict(self):
        try:
            self.to_dict()
            return True
        except:
            return False

    def to_yaml(self) -> str:
        import ruamel.yaml
        return ruamel.yaml.round_trip_dump(self.to_dict())


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
    def group_path(self):
        return '/'.join(self.keys if self.keys else ())

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Groups & Options                                                      #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def get_subgroup(self, key: str) -> 'Group':
        node = self.get_child(key)
        if not isinstance(node, Group):
            raise TypeError(f'node with key: {repr(key)} is not a {Group.__name__}')
        return node

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

    def new_subgroup(self, key: str) -> 'Group':
        return self.add_subgroup(key, Group())

    # we don't support new_option because we shouldn't
    # modify it after it is initialised
    # def new_option(self, key: str) -> 'Option':
    #     return self.add_option(key, Option())

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

    def get_subgroups_recursive(self, keys: List[str], make_missing=False) -> 'Group':
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
        group_keys, is_relative = s.split_group_path(path)
        # get the group corresponding to the path - must handle relative & root paths
        root = (self if is_relative else self.root)
        return root.get_subgroups_recursive(group_keys, make_missing=make_missing)

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

    def debug_print_tree(self, colors=True, show_options=True, full_option_path=True, full_group_path=True):
        from attr import dataclass

        @dataclass
        class _WalkObj:
            node: _ConfigObject
            visited: bool
            is_last: bool
            @property
            def is_group(self):
                return isinstance(self.node, Group)
            @property
            def has_groups_after(self):
                return self.node.has_parent and isinstance(self.node.parent, Group) and bool(self.node.parent.groups)
            @property
            def key(self):
                return (self.is_group, self.visited, self.is_last, self.has_groups_after)
            def __str__(self):
                return f":{''.join(map(str, map(int, self.key)))}"

        def _is_last_iter(items):
            yield from ((item, i == len(items)-1) for i, item in enumerate(items))

        def _walk():
            def _recurse(node, is_last, stack):
                stk = stack + [_WalkObj(node, False, is_last)]
                yield stk
                stk[-1].visited = True
                if isinstance(node, Group):
                    if show_options:
                        for o, l in _is_last_iter(node.options.values()):
                            yield from _recurse(o, l, stk)
                    for g, l in _is_last_iter(node.groups.values()):
                        yield from _recurse(g, l, stk)
            return _recurse(self, True, [])

        if colors:
            nG, nO, S, G, O, R = '\033[35m', '\033[33m', '\033[90m', '\033[95m', '\033[93m', '\033[0m'
        else:
            nG, nO, S, G, O, R = '', '', '', '', '', ''

        TREE = {
            (1, 1, 1, 0): f'   ',           # group,  visited,   last,  has groups after
            (1, 1, 1, 1): f'   ',           # group,  visited,   last,  no groups after
            (1, 0, 1, 0): f'   ',           # group,  unvisited, last,  has groups after
            (1, 1, 0, 1): f' {S}│{R} ',     # group,  visited,   inner, no groups after
            (1, 0, 0, 1): f' {S}├{G}─{R}',  # group,  unvisited, inner, no groups after
            (1, 0, 1, 1): f' {S}╰{G}─{R}',  # group,  unvisited, last,  no groups after
            (0, 0, 0, 1): f' {S}│{R} ',     # option, unvisited, last,  has groups after
            (0, 0, 1, 1): f' {S}├{O}╌{R}',  # option, unvisited, last,  no groups after
            (0, 0, 0, 0): f' {S}├{O}╌{R}',  # option, unvisited, inner, has groups after
            (0, 0, 1, 0): f' {S}╰{O}╌{R}',  # option, unvisited, last,  has groups after
        }

        for stack in _walk():
            (*_, item) = stack
            tree = ''.join(TREE.get(o.key, f'ERR{o}') for o in stack[1:])
            if item.is_group:
                keys = [f'/{k}' for k in (item.node.keys if item.node.keys else ('',))]
                name = f"{nG}{keys[-1]}{R}"
                if full_group_path:
                    name = f"{S}{''.join(keys[:-1])}{R}" + name
            else:
                name = f"{nO}{item.node.key}{R}"
                if full_option_path:
                    name = f"{S}{('/' + '/'.join(item.node.keys[:-1]))}:{R} " + name
            print(tree, name)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Schema                                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @classmethod
    def from_dict(cls, raw_group: dict, validate=True):
        if validate:
            raw_group = s.VerboseGroup.validate(raw_group)
        group = Group()
        for key, child in raw_group[s.KEY_CHILDREN].items():
            if child[s.KEY_TYPE] == s.TYPE_GROUP:
                group.add_subgroup(key, Group.from_dict(child, validate=False))
            elif child[s.KEY_TYPE] == s.TYPE_OPTION:
                group.add_option(key, Option.from_dict(child, validate=False))
            else:
                raise ValueError(f'Invalid type: {child[s.KEY_TYPE]}')
        return group

    def to_dict(self, validate=True):
        group = {
            s.KEY_TYPE: s.TYPE_GROUP,
            s.KEY_CHILDREN: {k: self[k].to_dict(validate=False) for k in self}
        }
        return s.VerboseGroup.validate(group) if validate else group


# ========================================================================= #
# Option                                                                    #
# ========================================================================= #


class Option(_ConfigObject):

    def __init__(
            self,
            data: dict = None,
            pkg: str = None,
            include: Dict[str, str] = None,
    ):
        super().__init__()
        self._data = data if data is not None else {}
        self._pkg = pkg if pkg is not None else s.DEFAULT_PKG
        self._include = include if include is not None else {}
        assert isinstance(self._pkg, (str, ConfigNode)), f'{s.KEY_PKG} is not a string or {ConfigNode.__name__}'
        assert isinstance(self._data, dict), f'{s.KEY_DATA} is not a dictionary'
        assert isinstance(self._include, dict), f'{s.KEY_MERGE} is not a dicitonary'
        # we dont validate in case things are nodes

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
    def group_path(self):
        return self.group.group_path

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

    def get_unresolved_includes(self):
        return self._ReplaceStrings().transform(self._include)

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
        return f'{self.__class__.__name__}({self._data})'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # schema                                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @classmethod
    def from_dict(cls, option, validate=True):
        if validate:
            option = s.VerboseOption.validate(option)
        return Option(
            pkg=option[s.KEY_PKG],
            include=option[s.KEY_MERGE],
            data=option[s.KEY_DATA],
        )

    def to_dict(self, validate=True):
        option = {
            s.KEY_TYPE: s.TYPE_OPTION,
            s.KEY_PKG: self._pkg,
            s.KEY_MERGE: self._include,
            s.KEY_DATA: self._data,
        }
        return s.VerboseOption.validate(option) if validate else option


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

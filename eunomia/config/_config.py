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
        return self._key and self._parent

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
        return tuple(n.key for n in self._walk_from_root(visit_root=False))

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

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Strings                                                               #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f'{self.__class__.__name__}({self._children})'

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
            opts: Dict[str, str] = None,
    ):
        super().__init__()
        self._data = data if data is not None else {}
        self._pkg = pkg if pkg is not None else s.DEFAULT_PKG
        self._opts = opts if opts is not None else {}
        assert isinstance(self._pkg, (str, ConfigNode)), f'{s.KEY_PKG} is not a string or {ConfigNode.__name__}'
        assert isinstance(self._data, dict), f'{s.KEY_DATA} is not a dictionary'
        assert isinstance(self._opts, dict), f'{s.KEY_OPTS} is not a dicitonary'
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

    def get_unresolved_options(self):
        return self._ReplaceStrings().transform(self._opts)

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
    __iter__ = None

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
            opts=option[s.KEY_OPTS],
            data=option[s.KEY_DATA],
        )

    def to_dict(self, validate=True):
        option = {
            s.KEY_TYPE: s.TYPE_OPTION,
            s.KEY_PKG: self._pkg,
            s.KEY_OPTS: self._opts,
            s.KEY_DATA: self._data,
        }
        return s.VerboseOption.validate(option) if validate else option


# ========================================================================= #
# End                                                                       #
# ========================================================================= #
from typing import Union, Dict, List, Tuple

from eunomia.config import Option, Group
from eunomia.config import keys as K
from eunomia.config import validate as V
from eunomia.config.nodes import SubNode, ConfigNode
from eunomia.util._util_traverse import Transformer


# ========================================================================= #
# Defaults Entry                                                            #
# ========================================================================= #


OorS = Union[Group, Option, str]
GorS = Union[Group, Option, str]
GorOorS = Union[Group, Option, str]

InputDefaultType = Union[
    'Default',
    # we can infer lhs, this is the rhs
    # -- this is converted to below
    GorOorS,
    # lhs must be direct parent of rhs, more verbose
    Dict[GorOorS, Union[GorOorS, List[OorS]]],
]


# ========================================================================= #
# Defaults Entry                                                            #
# ========================================================================= #


class DefaultTransformer(Transformer):

    # TODO: this could be cleaned up a lot...
    #       very manual at the moment...

    def __init__(self, in_opt: Option, resolver, force_substitute=True):
        self._in_opt = in_opt
        self._resolver = resolver
        self._force_resolve = force_substitute

    def __transform_default__(self, value):
        if isinstance(value, ConfigNode):
            return self._transform_str(value)
        raise TypeError(f'unsupported type trying to transform default item: {value}')

    def _transform_str(self, string):
        # handle special value
        if string == K.OPT_SELF:
            raise RuntimeError(f'this is a bug, {K.OPT_SELF} should be handled before being transformed!')
        if string in K.ALL_OPT_ALIASES:
            raise RuntimeError(f'{repr(string)} is not allowed as a single string in defaults. Must be a value after a group.')
        object = self._resolve(string, from_group=self._in_opt.group)
        # this check should never fail
        assert isinstance(object, (Option, Group))
        # continue transforming
        return self.transform(object)

    def _transform_Group(self, group: Group):
        return group, list(group.options.values())

    def _transform_Option(self, option: Option):
        return option.group, [option]

    def _transform_dict(self, dct: dict):
        # checks
        if len(dct) != 1:
            raise ValueError(f'dict default entry {dct} must contain only one key.')
        ((group, opts),) = dct.items()
        assert not isinstance(group, dict)
        assert not isinstance(opts, dict)
        # resolve keys & handle glob
        if isinstance(group, str):
            group = self._resolve(group, from_group=self._in_opt.group)
        if not isinstance(group, Group):
            raise KeyError(f'defaults entry has key that is not a group or path to a group: {group.abs_path}')
        # resolve values
        if isinstance(opts, (str, ConfigNode)):
            opts = group if (opts == K.OPT_GLOB) else self._resolve(opts, from_group=group)
            assert isinstance(opts, (Group, Option))
        if isinstance(opts, (Group, Option)):
            _, opts = self.transform(opts)
            assert isinstance(opts, list)
        # checks
        assert isinstance(group, (Group, Option))
        assert isinstance(opts, list)
        group: Union[Group, Option]
        # continue resolving,
        options: List[Option] = []
        for opt in opts:
            if isinstance(opt, (str, ConfigNode)):
                opt = self._resolve(opt, from_group=group)
            if not isinstance(opt, Option):
                raise KeyError(f'defaults entry has value in list that is not an option {repr(opt.abs_path)}. All values given in a list are expected to point to options!')
            options.append(opt)
        # return finally!
        return group, options

    def _resolve(self, string, from_group: Group) -> Union[Group, Option]:
        if string in K.ALL_OPT_ALIASES:
            raise RuntimeError(f'{string} cannot be nested in a defaults entry!')
        # resolve
        if self._force_resolve:
            string = string if isinstance(string, ConfigNode) else SubNode(string)
        if isinstance(string, ConfigNode):
            if self._resolver:
                string = self._resolver(string)
        # checks
        if not isinstance(string, str):
            raise TypeError(f'default string did not resolve as a string! Invalid: {repr(string)}')
        if string in K.ALL_OPT_ALIASES:
            raise RuntimeError(f'defaults are not allowed to resolve to {string}! Invalid: {repr(string)}')
        # get config object
        return from_group.get_child_recursive(string)


class Default(object):

    def __init__(self, default: InputDefaultType, pkg_override=None):
        self._default = default
        # check override
        self._pkg_override = pkg_override
        if pkg_override is not None:
            if not isinstance(pkg_override, str):
                raise TypeError(f'pkg_override must be a string. Invalid: {pkg_override}')
            V.split_package_path(pkg_override)

    @staticmethod
    def make_self():
        return Default(K.OPT_SELF)

    @property
    def is_self_pre_resolve(self):
        return self._default == K.OPT_SELF

    def to_resolved_components(self, in_opt: Option, resolver, force_substitute=True) -> Tuple[Group, List[Option], Tuple[str, ...], bool]:
        if self.is_self_pre_resolve:
            is_self = True
            # get values
            parent, children = in_opt, [in_opt]
        else:
            is_self = False
            # get values
            parent, children = DefaultTransformer(in_opt, resolver, force_substitute=force_substitute).transform(self._default)
            # check parents and children
            assert isinstance(parent, (Group, Option))
            assert all(isinstance(child, Option) for child in children)
            assert all((child.parent is parent) for child in children)
            assert len(set(child.abs_path for child in children)) == len(children)
            # get other values
        # resolve the package
        pkg_keys = parent.get_package_keys(self._pkg_override)
        # return the values!
        return parent, children, pkg_keys, is_self

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self._default)})'



# ========================================================================= #
# End                                                                       #
# ========================================================================= #

from collections import defaultdict
from typing import Dict, Union, DefaultDict, List, Tuple

from eunomia.config import Group, Option
from eunomia.config import scheme as s

from eunomia.registry.util import make_target_dict, _fn_get_module_path, _camel_to_snake
from eunomia._util_dict import recursive_getitem, dict_recursive_update


# ========================================================================= #
# Advanced Group                                                            #
# ========================================================================= #


class RegistryGroup(Group):

    """
    This group allows registration of functions or classes, constructing an
    option that has the _target_ parameter set, with default values obtained
    from the default parameters of the function.

    The option by default resides under the group that corresponds to the module
    that the function or class resides in.
    """

    def __init__(
            self,
            named_nodes: Dict[str, Union['Group', 'Option']] = None,
    ):
        super().__init__(named_nodes=named_nodes)
        # save all default options
        self._registered_all: DefaultDict[object, List[Option]] = defaultdict(list)
        self._registered_defaults: Dict[object, Tuple[bool, Option]] = {}

    def register_target(
            self,
            fn=None,
            # config settings
            name: str = None, path: str = None, is_default: bool = None,
            # target function
            target: str = None, params: dict = None, mode: str = 'any', keep_defaults: bool = True,
            # option params extras
            nest_path: str = None, data: dict = None, pkg: str = None, defaults: dict = None
    ):
        def wrapper(func):
            self.register_target_fn(
                func,
                name=name, path=path, is_default=is_default,
                target=target, params=params, mode=mode, keep_defaults=keep_defaults,
                nest_path=nest_path, data=data, pkg=pkg, defaults=defaults,
            )
            return func
        # decorate correctly!
        if fn is not None:
            return wrapper(fn)
        else:
            return wrapper

    def register_target_fn(
            self,
            fn,
            # config settings
            name: str = None, path: str = None, is_default: bool = None,
            # target function
            target: str = None, params: dict = None, mode: str = 'any', keep_defaults: bool = True,
            # option params extras
            nest_path: str = None, data: dict = None, pkg: str = None, defaults: dict = None
    ) -> 'RegistryGroup':
        assert not self.has_parent, 'Can only register on the root node.'
        # get various defaults
        path = _fn_get_module_path(fn) if path is None else path
        name = _camel_to_snake(fn.__name__) if name is None else name
        data = {} if data is None else data
        # check nest path
        if nest_path is not None:
            nest_path, is_relative = s.split_pkg_path(nest_path)
            assert not is_relative, 'nest path must not be relative'
        else:
            nest_path = []
        # get the dictionary to merge the target into
        targ_merge_dict = recursive_getitem(data, nest_path, make_missing=True)
        if not isinstance(targ_merge_dict, dict):
            raise ValueError('nested object in data must be a dictionary that the target can be merged into.')
        if targ_merge_dict:
            raise ValueError('nested object in data must be empty, otherwise target conflicts can occur.')
        # make data for the option
        dict_recursive_update(
            left=targ_merge_dict,
            right=make_target_dict(fn, target=target, params=params, mode=mode, keep_defaults=keep_defaults),
        )
        # make option under the specified group
        group = self.get_group_from_path(path=path, make_missing=True)
        option = group.add_option(name, Option(
            data=data,
            pkg=pkg,
            defaults=defaults
        ))
        # register the option first!
        try:
            self._register_obj(fn, option, is_default)
        except Exception as e:
            group.del_option(name)
            raise e
        # done!
        return self

    def _register_obj(self, func, option, is_default=None):
        assert not self.has_parent, 'Can only register on the root node.'
        # register as a default
        if func in self._registered_defaults:
            explicit, _ = self._registered_defaults[func]
            if explicit:
                if is_default:
                    raise AssertionError(f'registered callable {func} for option: {option.keys} was previously explicitly registered as a default.')
            else:
                if is_default:
                    self._registered_defaults[func] = (True, option)
                elif is_default is None:
                    self._registered_defaults.setdefault(func, (False, option))
        else:
            if is_default or (is_default is None):
                self._registered_defaults.setdefault(func, (False if is_default is None else True, option))
        # keep track that this was registered
        self._registered_all[func].append(option)

    def get_registered_defaults(self, explicit_only=False):
        assert not self.has_parent, 'Can only register on the root node.'
        # get default options!
        defaults = {}
        for func, (explicit, option) in self._registered_defaults.items():
            if explicit_only and not explicit:
                continue
            k = option.group_path
            if k in defaults:
                raise AssertionError(f'default for callable {func} corresponding to option: {option.keys} has already been added.')
            defaults[k] = option.key
        return defaults


# ========================================================================= #
# END                                                                       #
# ========================================================================= #


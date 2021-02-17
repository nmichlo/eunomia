from collections import defaultdict
from typing import Dict, Union, DefaultDict, List, Tuple

from eunomia.config import Group, Option
from eunomia.registry.util import _fn_get_module_path, _camel_to_snake, make_target_option


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
            nest_path: str = None, data: dict = None, pkg: str = None, defaults: list = None
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
            nest_path: str = None, data: dict = None, pkg: str = None, defaults: list = None
    ) -> 'Option':
        assert not self.has_parent, 'Can only register on the root node.'
        # make various defaults
        path = _fn_get_module_path(fn) if path is None else path
        name = _camel_to_snake(fn.__name__) if name is None else name
        # make option under the specified group
        group = self.get_group_recursive(path=path, make_missing=True)
        option = group.add_option(name, make_target_option(
            fn, target=target, params=params, mode=mode, keep_defaults=keep_defaults,
            nest_path=nest_path, data=data, pkg=pkg, defaults=defaults
        ))
        # register the option first!
        try:
            self._register_obj(fn, option, is_default)
        except Exception as e:
            group.del_option(name)
            raise e
        # done!
        return option

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

    def get_registered_defaults(self, explicit_only=False) -> list:
        assert not self.has_parent, 'Can only register on the root node.'
        # get default options!
        defaults = {}
        for func, (explicit, option) in self._registered_defaults.items():
            if explicit_only and not explicit:
                continue
            k = option.abs_group_path
            if k in defaults:
                raise AssertionError(f'default for callable {func} corresponding to option: {option.keys} has already been added.')
            defaults[k] = option.key
        return [{k: v} for k, v in defaults.items()]


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

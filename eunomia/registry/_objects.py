import inspect
import os
import re
from collections import defaultdict
from typing import Dict, Union, DefaultDict, List, Tuple

from eunomia.config import Group, Option
from eunomia.config import scheme as s


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def _fn_get_kwargs(func) -> dict:
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }

def _fn_get_args(func) -> list:
    signature = inspect.signature(func)
    return [
        k
        for k, v in signature.parameters.items()
        if v.default is inspect.Parameter.empty
    ]

def _fn_get_all_args(func) -> list:
    signature = inspect.signature(func)
    return list(signature.parameters.keys())


def _fn_get_module_path(obj):
    path = os.path.relpath(inspect.getmodule(obj).__file__, os.getcwd())
    assert path.endswith('.py')
    path = path[:-len('.py')]
    return os.path.normpath(path)


def _fn_get_import_path(obj):
    module_path = '.'.join(_fn_get_module_path(obj).split('/'))
    return f'{module_path}.{obj.__name__}'


def _camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


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

    def register(
            self,
            # config settings
            option_name: str = None,
            group_path: str = None,
            is_default: bool = None,
            # target function
            target: str = None,
            override_params: dict = None,
            override_mode: str = 'any',
            include_kwargs: bool = True,
    ):
        def wrapper(func):
            self.register_fn(
                func,
                option_name=option_name,
                group_path=group_path,
                is_default=is_default,
                target=target,
                override_params=override_params,
                override_mode=override_mode,
                include_kwargs=include_kwargs,
            )
            return func
        # decorate correctly!
        if callable(option_name):
            fn, option_name = option_name, None
            return wrapper(fn)
        else:
            return wrapper

    def register_fn(
            self,
            func,
            # config settings
            option_name: str = None,
            group_path: str = None,
            is_default: bool = None,
            # target function
            target: str = None,
            override_params: dict = None,
            override_mode: str = 'any',
            include_kwargs: bool = True,
    ) -> 'RegistryGroup':
        assert not self.has_parent, 'Can only register on the root node.'
        # get various defaults
        group_path = _fn_get_module_path(func) if group_path is None else group_path
        option_name = _camel_to_snake(func.__name__) if option_name is None else option_name
        # make option under the specified group
        group = self.get_group_from_path(path=group_path, make_missing=True)
        data = self._get_func_target_data(
            func,
            target=target,
            override_params=override_params,
            override_mode=override_mode,
            include_kwargs=include_kwargs
        )
        option = group.add_option(option_name, Option(data=data))
        # register the option first!
        try:
            self._register_obj(func, option, is_default)
        except Exception as e:
            group.del_option(option_name)
            raise e
        # alright!
        return self

    def _get_func_target_data(
            self,
            func,
            target: str = None,
            override_params: dict = None,
            override_mode: str = 'any',
            include_kwargs: bool = True,
    ):
        # get default values
        target = _fn_get_import_path(func) if target is None else target
        overrides = {} if override_params is None else override_params
        # if we should include all the non-overridden default
        # parameters in the final config
        if include_kwargs:
            defaults = _fn_get_kwargs(func)
        else:
            defaults = {}
        # get the parameters that can be overridden
        args, kwargs, all_args = _fn_get_args(func), _fn_get_kwargs(func), _fn_get_all_args(func)
        if override_mode == 'kwargs':
            allowed_overrides = set(kwargs)
        elif override_mode == 'any':
            allowed_overrides = set(args) | set(kwargs)
        elif override_mode == 'all':
            allowed_overrides = set(args) | set(kwargs)
        else:
            raise KeyError(f'Invalid override mode: {repr(override_mode)}')
        # generate final list of parameter overrides
        for k in all_args:  # sorted
            if k in allowed_overrides:
                if k in overrides:
                    defaults[k] = overrides.pop(k)
        # check that no extra unused overrides exist
        # and that _target_ is not a parameter name
        assert not overrides, f'cannot override params: {list(overrides.keys())}'
        assert s.MARKER_KEY_TARGET not in defaults, f'object {target} has conflicting optional parameter: {s.MARKER_KEY_TARGET}'
        # check that nothing is left over according to the override mode
        if override_mode == 'all':
            missed_args = set(args) - set(defaults)
            if missed_args:
                missed_args = [a for a in all_args if a in missed_args]  # sorted
                raise AssertionError(f'all non-default parameters require an override: {missed_args}')
        # return final dictionary
        return {
            s.MARKER_KEY_TARGET: target,
            **defaults,
        }

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


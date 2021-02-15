import inspect
import os
import re

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


def make_target_dict(
        func,
        target: str = None,
        params: dict = None,
        mode: str = 'any',
        keep_defaults: bool = True,
) -> dict:
    # get default values
    target = _fn_get_import_path(func) if target is None else target
    overrides = {} if params is None else params
    # if we should include all the non-overridden default
    # parameters in the final config
    if keep_defaults:
        defaults = _fn_get_kwargs(func)
    else:
        defaults = {}
    # get the parameters that can be overridden
    args, kwargs, all_args = _fn_get_args(func), _fn_get_kwargs(func), _fn_get_all_args(func)
    if mode == 'kwargs':
        allowed_overrides = set(kwargs)
    elif mode == 'any':
        allowed_overrides = set(args) | set(kwargs)
    elif mode == 'all':
        allowed_overrides = set(args) | set(kwargs)
    else:
        raise KeyError(f'Invalid override mode: {repr(mode)}')
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
    if mode == 'all':
        missed_args = set(args) - set(defaults)
        if missed_args:
            missed_args = [a for a in all_args if a in missed_args]  # sorted
            raise AssertionError(f'all non-default parameters require an override: {missed_args}')
    # return final dictionary
    return {
        s.MARKER_KEY_TARGET: target,
        **defaults,
    }


# ========================================================================= #
# END                                                                       #
# ========================================================================= #


import inspect
import re

from eunomia._util_dict import recursive_getitem, dict_recursive_update
from eunomia.config import keys as K
from eunomia.config import validate as V
from eunomia.config import Option


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
    # get package search paths
    import os
    import sys
    # get module path
    path = os.path.abspath(inspect.getmodule(obj).__file__)
    # return the shortest relative path from all the packages
    rel_paths = []
    for site in sys.path:
        site = os.path.abspath(site)
        if os.path.commonprefix([site, path]) == site:
            rel_paths.append(os.path.relpath(path, site))
    # get shortest rel path
    rel_paths = sorted(rel_paths, key=str.__len__)
    assert len(rel_paths) > 0, f'no valid path found to: {obj}'
    # get the correct path
    path = rel_paths[0]
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


def make_target_option(
        fn,
        # target function
        target: str = None,
        params: dict = None,
        mode: str = 'any',
        keep_defaults: bool = True,
        # option params extras
        nest_path: str = None,
        data: dict = None,
        pkg: str = None,
        defaults: dict = None,
) -> 'Option':
    # get various defaults
    data = {} if data is None else data

    # check nest path
    if nest_path is not None:
        nest_path, is_relative = V.split_package_path(nest_path)
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

    # make option
    return Option(
        data=data,
        pkg=pkg,
        defaults=defaults
    )


def make_target_dict(
        func,
        # target function
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
    elif mode == 'unchecked':
        allowed_overrides = None
    else:
        raise KeyError(f'Invalid override mode: {repr(mode)}')

    # generate final list of parameter overrides
    if mode == 'unchecked':
        defaults.update(overrides)
        overrides = {}
    else:
        for k in all_args:  # sorted
            if k in allowed_overrides:
                if k in overrides:
                    defaults[k] = overrides.pop(k)

    # check that no extra unused overrides exist
    # and that _target_ is not a parameter name
    assert not overrides, f'cannot override params: {list(overrides.keys())}'
    assert K.MARKER_KEY_TARGET not in defaults, f'object {target} has conflicting optional parameter: {K.MARKER_KEY_TARGET}'

    # check that nothing is left over according to the override mode
    if mode == 'all':
        missed_args = set(args) - set(defaults)
        if missed_args:
            missed_args = [a for a in all_args if a in missed_args]  # sorted
            raise AssertionError(f'all non-default parameters require an override: {missed_args}')

    # return final dictionary
    return {
        K.MARKER_KEY_TARGET: target,
        **defaults,
    }


# ========================================================================= #
# END                                                                       #
# ========================================================================= #


import inspect
import importlib
import re
from copy import deepcopy

from eunomia.util._util_dict import recursive_getitem, dict_recursive_update
from eunomia.util._util_traverse import RecursiveTransformer
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
# Make Targets                                                              #
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
        defaults: list = None,
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
        safe_merge=False,
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
# Instantiate Targets                                                       #
# ========================================================================= #


def import_module_attr(target):
    # check the keys
    try:
        keys = V.validate_identifier_list(str.split(target, '.'))
    except Exception as e:
        raise ValueError(f'target {repr(target)} must contain at least one module component, and one attribute component eg: "math.log" or one builtin eg: "dict". Given target is: {repr(target)}').with_traceback(e.__traceback__)
    # special case, handle all builtins like dict or list
    if len(keys) < 1: # pragma: no cover
        raise RuntimeError('This is a bug and should not happen!')
    if len(keys) < 2:
        keys = ['builtins'] + keys
    # [1, len) : leaves at least one module keys, and at least one attr keys. Never empty
    for i in reversed(range(1, len(keys))):
        module_keys, attr_keys = keys[:i], keys[i:]
        # get the module, importlib cant import attributes on modules.
        try:
            module = importlib.import_module('.'.join(module_keys))
        except:
            continue
        # get the attr on the module
        obj = module
        try:
            for attr in attr_keys:
                obj = getattr(obj, attr)
        except AttributeError as e:
            raise AttributeError(f'could not import target {repr(target)}. {e}')
        return obj
    # we failed...
    raise ImportError(f'could not import target {repr(target)}. Are you sure the import module is correct?')


class _InstantiateTransformer(RecursiveTransformer):

    def __init__(self, recursive: bool = True):
        self._recursive = recursive
        self._visited = False

    def transform(self, value):
        # if not recursive, only go one layer deep
        if not self._recursive:
            if self._visited:
                return value
            self._visited = True
        # recurse like usual!
        return super().transform(value)

    def __transform_default__(self, value):
        # we dont throw an error if we encounter an unknown type
        return value

    def _transform_dict(self, config):
        # transform like usual
        config = super()._transform_dict(config)
        # return early
        if K.MARKER_KEY_TARGET not in config:
            return config
        # get args and kwargs
        target = config.pop(K.MARKER_KEY_TARGET)
        args = config.pop(K.MARKER_KEY_ARGS, ())
        kwargs = config.pop(K.MARKER_KEY_KWARGS, config)
        # if kwargs key existed in the config
        # check that config is empty after popping everything
        if (kwargs is not config) and config:
            raise KeyError(f'target dictionary contains the {K.MARKER_KEY_KWARGS} key as well as unused keys, which otherwise would be extracted as the kwargs. Choose one mode or the other.')
        # import & call
        fn = import_module_attr(target)
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f'Could not call target {repr(target)} object {fn} with args: {args} and kwargs: {kwargs}').with_traceback(e.__traceback__)


def instantiate(config, recursive=True, ensure_root_target=True):
    # if the root must be a dictionary and valid target
    if ensure_root_target:
        if not isinstance(config, dict):
            raise TypeError(f'Could not instantiate root object: not a dictionary! Otherwise set ensure_root_target=False')
        if K.MARKER_KEY_TARGET not in config:
            raise KeyError(f'Could not instantiate root object: target marker key {repr(K.MARKER_KEY_TARGET)} not found in root! Otherwise set ensure_root_target=False')
    # WARNING: this can mutate the given config
    config = deepcopy(config)
    # transform!
    return _InstantiateTransformer(recursive=recursive).transform(config)


call = instantiate


# ========================================================================= #
# END                                                                       #
# ========================================================================= #


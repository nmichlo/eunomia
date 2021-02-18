import keyword as _keyword
from typing import Union as _Union, Tuple as _Tuple, Dict as _Dict, List as _List

from eunomia.config import keys as _K


# ========================================================================= #
# Keys                                                                      #
# ========================================================================= #


def validate_identifier(key) -> str:
    if not isinstance(key, str):
        raise TypeError(f'identifier is not a string type: {type(key)}')
    if not key:
        raise ValueError(f'identifier cannot be empty: {repr(key)}')
    if not str.isidentifier(key):
        raise ValueError(f'identifier is not a valid python identifier: {repr(key)}')
    if _keyword.iskeyword(key):
        raise ValueError(f'identifier is a python keyword: {repr(key)}')
    return key


def validate_identifier_list(keys) -> list:
    if not isinstance(keys, list):
        raise TypeError(f'identifier list must be a list type: {type(keys)}')
    for k in keys:
        validate_identifier(k)
    return keys


def validate_config_identifier(key) -> str:
    key = validate_identifier(key)
    if key in _K.RESERVED_KEYS:
        raise ValueError(f'identifier is eunomia reserved key: {repr(key)}')
    if key.startswith('__') and key.endswith('__'):
        raise ValueError(f'identifier is reserved: {repr(key)}')
    return key


def validate_config_identifier_list(keys) -> list:
    if not isinstance(keys, list):
        raise TypeError(f'identifier list must be a list type: {type(keys)}')
    for k in keys:
        validate_config_identifier(k)
    return keys


# ========================================================================= #
# Values                                                                    #
# ========================================================================= #


def _split_path(path: str, sep: str) -> (str, bool):
    # check and remove prefix
    is_prefixed = False
    if path.startswith(sep):
        is_prefixed, path = True, path[len(sep):]
    # split path
    if path:
        split = str.split(path, sep)
    else:
        split = []
    # check identifiers
    return validate_config_identifier_list(split), is_prefixed


def split_package_path(path: str) -> (str, bool):
    if path in _K.ALL_PACKAGE_ALIASES:
        raise RuntimeError('special package keys should be handled separately')
    keys, is_relative = _split_path(path, '.')
    return keys, is_relative


def split_config_path(path: str) -> (str, bool):
    keys, is_not_relative = _split_path(path, '/')
    return keys, not is_not_relative


# ========================================================================= #
# Paths                                                                     #
# ========================================================================= #


def validate_package_path(path) -> str:
    if not isinstance(path, str):
        raise TypeError(f'package path is not of type string: {type(path)}')
    # check for aliases
    if path in _K.ALL_PACKAGE_ALIASES:
        return path
    # try split
    split_package_path(path)
    return path


def validate_config_path(path) -> str:
    if not isinstance(path, str):
        raise TypeError(f'config path is not of type string: {path}')
    # try split
    split_config_path(path)
    return path


# ========================================================================= #
# config values                                                             #
# ========================================================================= #


def validate_option_data(data) -> dict:
    if data is None:
        return {}

    from eunomia.config.nodes import ConfigNode

    if isinstance(data, ConfigNode):
        raise TypeError(f'option data object can never be a config node: {repr(data)}')
    if not isinstance(data, dict):
        raise TypeError(f'option data object must be of type dict: {repr(data)}')
    return _validate_option_data(data)


def _validate_option_data(value):
    if value is None:
        pass
    elif isinstance(value, dict):
        for k, v in value.items():
            validate_config_identifier(k)
            _validate_option_data(v)
    elif isinstance(value, (list, tuple, set)):
        for v in value:
            _validate_option_data(v)
    elif isinstance(value, (int, float, str)):
        pass
    else:
        raise TypeError(f'unsupported data value type: {type(value)} with value: {repr(value)}')
    return value


def validate_option_package(pkg) -> str:
    if pkg is None:
        return _K.DEFAULT_PKG

    from eunomia.config.nodes import ConfigNode

    if isinstance(pkg, ConfigNode):
        raise TypeError(f'option package can never be a config node: {repr(pkg)}')
    try:
        return validate_package_path(pkg)
    except Exception as e:
        raise ValueError(f'option package is invalid: {repr(pkg)}').with_traceback(e.__traceback__)


def validate_option_defaults(defaults, allow_config_nodes=False) -> list:
    if defaults is None:
        return []

    from eunomia.config.nodes import ConfigNode

    if isinstance(defaults, ConfigNode):
        raise TypeError(f'option defaults can never directly be a config node, only its items: {repr(defaults)}')
    if not isinstance(defaults, list):
        raise TypeError('defualts must be a list of values')

    try:
        for default in defaults:
            validate_defaults_item(default, allow_config_nodes=allow_config_nodes)
    except Exception as e:
        raise ValueError(f'option defaults is invalid: {repr(defaults)}').with_traceback(e.__traceback__)

    return defaults


def validate_option_type(typ) -> str:
    if typ is None:
        return _K.TYPE_OPTION

    from eunomia.config.nodes import ConfigNode

    if isinstance(typ, ConfigNode):
        raise TypeError(f'option type can never be a config node: {repr(typ)}')
    if not isinstance(typ, str):
        raise TypeError(f'option type must be of type string: {repr(typ)}')
    if typ != _K.TYPE_OPTION:
        raise ValueError(f'option  type must be: {repr(typ)}')
    return typ


# ========================================================================= #
# Options                                                                   #
# ========================================================================= #


def validate_defaults_item(default, allow_config_nodes=False) -> _Union[str, _Dict[str, str], _Dict[str, _List[str]]]:
    from eunomia.config import Group, Option
    from eunomia.config.nodes import ConfigNode

    # we cant resolve options or defaults here in case the tree is modified after adding!
    # we can only resolve them at merge time!
    if isinstance(default, str):
        if default != _K.OPT_SELF:
            validate_config_path(default)
    elif isinstance(default, (Group, Option, ConfigNode)):
        if not allow_config_nodes:
            raise TypeError(f'{default.__class__.__name__} have been disabled as the group key for default entry. Invalid: {default}')
    elif isinstance(default, dict):
        # split
        if len(default) != 1:
            raise ValueError(f'if defaults entry is a dictionary it must have one and only one key. Invalid: {default}')
        ((group, opts),) = default.items()

        # check key
        if isinstance(group, str):
            validate_config_path(group)
        elif isinstance(group, Group):
            if not allow_config_nodes:
                raise TypeError(f'{group.__class__.__name__} have been disabled as the group key for default entry. Invalid: {group}')
        elif isinstance(group, ConfigNode):
            raise TypeError(f'substitution is not supported for the group key of a defaults entry: {group}')
        else:
            raise TypeError(f'unsupported defaults entry group key type. Invalid: {group}')

        # check value
        if isinstance(opts, str):
            if opts != _K.OPT_GLOB:
                validate_config_path(opts)
        elif isinstance(opts, (Group, Option, ConfigNode)):
            if not allow_config_nodes:
                raise TypeError(f'{opts.__class__.__name__} have been disabled as the option values for default entry. Invalid: {opts}')
        elif isinstance(opts, list):
            for opt in opts:
                if isinstance(opt, str):
                    validate_config_path(opt)
                elif isinstance(opt, Option):
                    if not allow_config_nodes:
                        raise TypeError(f'{opts.__class__.__name__} have been disabled as the item in option value list for default entry. Invalid: {opts}')
                else:
                    raise TypeError(f'unsupported item in defaults entry value list type. Invalid: {opts}')
        else:
            raise TypeError(f'unsupported defaults entry group value type {type(opts)} with value {opts}')
        # done!
    else:
        raise TypeError(f'default entry is invalid type {type(default)}, can only be string paths, {Group.__name__}s or {Option.__name__}s, or a dictionary containing those.')
    return default


def keys_as_abs_config_path(keys: _Union[_Tuple[str], _List[str]]) -> str:
    return validate_config_path('/' + '/'.join(keys))


def keys_as_abs_pkg_path(keys: _Union[_Tuple[str], _List[str]]) -> str:
    return validate_package_path('.'.join(keys))


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

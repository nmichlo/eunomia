import os as _os
import keyword as _keyword
from eunomia.config import keys as K


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
    if key in K.RESERVED_KEYS:
        raise ValueError(f'identifier is eunomia reserved key: {repr(key)}')
    if key.startswith('__') and key.endswith('__'):
        raise ValueError(f'identifier is reserved: {repr(key)}')
    return key


def validate_identifier_list(keys) -> list:
    if not isinstance(keys, list):
        raise TypeError(f'identifier list must be a list type: {type(keys)}')
    for k in keys:
        validate_identifier(k)
    return keys


def validate_config_identifier(key) -> str:
    return validate_identifier(key)


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
    return validate_identifier_list(split), is_prefixed


def split_package_path(path: str) -> (str, bool):
    if path in {K.PKG_GROUP, K.PKG_ROOT}:
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
    if path in {K.PKG_GROUP, K.PKG_ROOT}:
        return path
    # try split
    split_package_path(path)
    return path


def validate_config_path(path) -> str:
    if not isinstance(path, str):
        raise TypeError(f'config path is not of type string: {type(path)}')
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
    if isinstance(value, list):
        for v in value:
            _validate_option_data(v)
    elif isinstance(value, dict):
        for k, v in value.items():
            validate_identifier(k)
            _validate_option_data(v)
    elif isinstance(value, (int, float, str)):
        pass
    else:
        raise TypeError(f'unsupported value type: {type(value)}')
    return value


def validate_option_package(pkg) -> str:
    if pkg is None:
        return K.DEFAULT_PKG

    from eunomia.config.nodes import ConfigNode

    if isinstance(pkg, ConfigNode):
        raise ValueError(f'option package can never be a config node: {repr(pkg)}')
    try:
        return validate_package_path(pkg)
    except:
        raise ValueError(f'option package is invalid: {repr(pkg)}')


def validate_option_defaults(defaults, allow_config_nodes=False) -> list:
    if defaults is None:
        return []

    from eunomia.config.nodes import ConfigNode

    if isinstance(defaults, ConfigNode):
        raise ValueError(f'option defaults can never directly be a config node, only its items: {repr(defaults)}')
    try:
        return split_defaults_list_items(defaults, allow_config_node_return=allow_config_nodes)
    except Exception as e:
        raise ValueError(f'option defaults is invalid: {repr(defaults)}').with_traceback(e.__traceback__)


# ========================================================================= #
# Options                                                                   #
# ========================================================================= #


def split_defaults_item(item, allow_config_node_return=False) -> (str, str):
    from eunomia.config.nodes import ConfigNode

    if isinstance(item, ConfigNode):
        raise TypeError('single item config nodes that represent a defaults item should be resolved before being split.')

    # check the normal types
    if item == K.OPT_SELF:
        group_path, option_name = K.OPT_SELF, K.OPT_SELF
        return group_path, option_name
    elif isinstance(item, (tuple, list)):
        group_path, option_name = item
    elif isinstance(item, str):
        option_name = _os.path.basename(item)
        group_path = _os.path.dirname(item)
    elif isinstance(item, dict):
        assert len(item) == 1
        group_path, option_name = list(item.items())[0]
    else:
        raise TypeError(f'invalid defaults item type: {type(item)}')

    # we allow this to return config nodes, but they need to be resolved
    if not allow_config_node_return:
        if isinstance(group_path, ConfigNode) or isinstance(option_name, ConfigNode):
            raise TypeError('returning of config nodes is not allowed')

    # validate identifiers
    if not isinstance(group_path, ConfigNode):
        group_path = validate_config_path(group_path)
    if not isinstance(option_name, ConfigNode):
        option_name = validate_config_identifier(option_name)

    # return!
    return group_path, option_name


def split_defaults_list_items(defaults, allow_config_node_return=False) -> list:
    if not isinstance(defaults, list):
        raise TypeError(f'defaults list must be of type: {list}')
    return [
        split_defaults_item(item, allow_config_node_return=allow_config_node_return)
        for item in defaults
    ]


def validate_resolved_defaults_item(group_path, option_name):
    from eunomia.config.nodes import ConfigNode

    if isinstance(group_path, ConfigNode) or isinstance(option_name, ConfigNode):
        raise ValueError('group_path and option_name have not been resolved')

    return validate_config_path(group_path), validate_config_identifier(option_name)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

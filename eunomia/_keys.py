import keyword
from functools import wraps
from typing import Union, NoReturn


# ========================================================================= #
# VALUES: Eunomia Paths & Packages                                          #
# ========================================================================= #


PKG_ALIAS_GROUP = '_path_'  # make current option package equal to the path for the group it is in
PKG_ALIAS_ROOT  = '_root_'  # makes the current option package the root

# which of the above is the default
PKG_DEFAULT_ALIAS = PKG_ALIAS_GROUP

# A list of special packages:
#   !! these should only be allowed as the values for
#      the KEY_PACKAGE key, not as keys themselves
PKG_ALIASES_ALL = {
    PKG_ALIAS_GROUP,
    PKG_ALIAS_ROOT,
}

# separators
SEP_PATHS = '/'
SEP_PACKAGES = '.'


# ========================================================================= #
# KEYS: Eunomia Config Keys                                                 #
# ========================================================================= #


KEY_GROUP   = '_group_'    # used for dictionaries to indicate that they are a group
KEY_PACKAGE = '_package_'  # options node name to change the current package
KEY_OPTIONS = '_options_'  # options node name to choose the option in a subgroup
KEY_PLUGINS = '_plugins_'  # options node name to choose and adjust various settings for plugins


# keys reserved for options only
#   !! these should not be allowed as keys in groups
KEYS_RESERVED_FOR_OPTION = {
    KEY_PACKAGE,
    KEY_OPTIONS,
    KEY_PLUGINS,
}
# keys reserved for groups only
#   !! these should not be allowed as keys in options
KEYS_RESERVED_FOR_GROUP = {
    KEY_GROUP,
}
# all reserved node keys
KEYS_RESERVED_ALL = {
    *KEYS_RESERVED_FOR_OPTION,
    *KEYS_RESERVED_FOR_GROUP,
}


# keys outright not allowed
# TODO: maybe lift these limitations? They are very restrictive. "keys", "items"
#       & "values" are popular names. Also package directives names could be useful.
KEYS_NOT_ALLOWED = {
    *PKG_ALIASES_ALL,
    *dir(dict)
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
# Helper                                                                    #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


def _overwrite_fn__false_on_error(func: callable, errors: tuple = (TypeError, ValueError)):
    def wrapper(ignore_fn):
        @wraps
        def inner(*args, **kwargs):
            try:
                func(*args, **kwargs)
                return True
            except errors:
                return False
        return inner
    return wrapper


# ========================================================================= #
# KEYS: Single Eunomia Keys                                                 #
# ========================================================================= #


def assert_valid_single_key(key: str) -> NoReturn:
    # check the types, that the key is a valid identifier,
    # and that it does not conflict with python.
    if not isinstance(key, str):
        raise TypeError(f'keys must be strings: {repr(key)}')
    if not str.isidentifier(key):
        raise ValueError(f'keys must be valid python identifiers: {repr(key)}')
    if keyword.iskeyword(key):
        raise ValueError(f'keys cannot be python keywords: {repr(key)}')

    # check that we do not conflict with reserved keys
    if key in PKG_ALIASES_ALL:
        raise ValueError(f'key is a special package alias and is not allowed: {repr(key)}')
    if key in KEYS_NOT_ALLOWED:
        raise ValueError(f'key is not allowed: {repr(key)}')


def assert_valid_single_option_key(key: str) -> NoReturn:
    # standard checks
    assert_valid_single_key(key)
    # make sure we don't contain any group keys
    if key in KEYS_RESERVED_FOR_GROUP:
        raise ValueError(f'key reserved for groups is not allowed in an option: {repr(key)}')


def assert_valid_single_group_key(key: str) -> NoReturn:
    # standard checks
    assert_valid_single_key(key)
    # make sure we don't contain any group keys
    if key in KEYS_RESERVED_FOR_OPTION:
        raise ValueError(f'key reserved for options is not allowed in a group: {repr(key)}')


def assert_valid_single_pkg_or_path_part(key: str) -> NoReturn:
    # standard checks
    assert_valid_single_key(key)
    # make sure we don't contain any group keys
    if key in KEYS_RESERVED_ALL:
        raise ValueError(f'key reserved for options or groups is not allowed as a package or path name: {repr(key)}')


@_overwrite_fn__false_on_error(assert_valid_single_key)
def is_valid_single_key(key: str) -> bool: pass
@_overwrite_fn__false_on_error(assert_valid_single_option_key)
def is_valid_single_option_key(key: str) -> bool: pass
@_overwrite_fn__false_on_error(assert_valid_single_group_key)
def is_valid_single_group_key(key: str) -> bool: pass
@_overwrite_fn__false_on_error(assert_valid_single_pkg_or_path_part)
def is_valid_single_pkg_or_path_part(key: str) -> bool: pass


# ========================================================================= #
# KEYS in VALUES: Eunomia Packages & Paths - Split                          #
# ========================================================================= #


def _split_keys(keys: Union[str, list[str], tuple[str]], sep: str, desc: str, allow_root_list=False) -> Union[list[str], tuple[str]]:
    if isinstance(keys, str):
        keys = keys.split(sep)
    if not isinstance(keys, (list, tuple)):
        raise TypeError(f'{desc}: {keys=} must be a str, list[str] or tuple[str]')
    if not allow_root_list:
        if not keys:
            raise ValueError(f'{desc}: {keys=} name must contain at least one group name')
    return keys


def _assert_split_components_valid(keys: list[str], desc: str):
    for key in keys:
        try:
            assert_valid_single_pkg_or_path_part(key)
        except Exception as e:
            raise e.__class__(f'{desc}: {repr(keys)} has invalid component: {repr(key)}\n{e}')


def split_valid_value_package(keys: Union[str, list, tuple], allow_root_list=False):
    """
    Checks if a value path listed in the _package_ node of a
    config group option is valid.
    - paths are separated by "."
    - does not allow reserved eunomia keys to be used
    - a singular package directive can be used defined in: PKG_ALIAS_GROUP or PKG_ALIAS_ROOT
    """
    keys = _split_keys(keys, SEP_PACKAGES, 'package', allow_root_list=allow_root_list)
    # exit early if equals alias
    if len(keys) == 1:
        if keys[0] in PKG_ALIASES_ALL:
            return keys
    _assert_split_components_valid(keys, 'package')
    return keys


def split_valid_value_path(keys: Union[str, list, tuple], allow_root_list=False):
    """
    Checks if a path to a config group or config group option
    is valid.
    - paths are separated by "/"
    - does not allow reserved eunomia keys to be used
    - does not allow package aliases like split_eunomia_package(...)
    """
    keys = _split_keys(keys, SEP_PATHS, 'path', allow_root_list=allow_root_list)
    _assert_split_components_valid(keys, 'path')
    return keys


# ========================================================================= #
# KEYS in VALUES: Eunomia Packages & Paths                                  #
# ========================================================================= #


def assert_valid_value_package(package: Union[str, list, tuple]) -> NoReturn:
    split_valid_value_package(package)


def assert_valid_value_path(path: Union[str, list, tuple]) -> NoReturn:
    split_valid_value_path(path)


@_overwrite_fn__false_on_error(split_valid_value_package)
def is_valid_value_package(path: Union[str, list, tuple]) -> bool: pass
@_overwrite_fn__false_on_error(split_valid_value_path)
def is_valid_value_path(path: Union[str, list, tuple]) -> bool: pass


# ========================================================================= #
# KEYS in VALUES: Joined Eunomia Keys                                       #
# ========================================================================= #


def join_valid_value_package(*keys: str):
    assert_valid_value_package(keys)
    package = SEP_PACKAGES.join(keys)
    return package


def join_valid_value_path(*keys: str):
    assert_valid_value_path(keys)
    path = SEP_PATHS.join(keys)
    return path


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

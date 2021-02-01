import keyword
from typing import Any, Union


# ========================================================================= #
# Eunomia Variables                                                         #
# ========================================================================= #


# options node name to change the current package
KEY_PACKAGE = '_package_'
# options node name to choose the option in a subgroup
KEY_OPTIONS = '_options_'
# all reserved node keys
ALL_RESERVED_KEYS = {KEY_PACKAGE, KEY_OPTIONS}
# keys outright not allowed
KEYS_NOT_ALLOWED = {
    # TODO: maybe lift this limitation? very restrictive.
    #       "keys", "items" & "values" are popular names
    *dir(dict)
}

# make current option package equal to the path for the group it is in
PACKAGE_GROUP = '_group_'
# makes the current option package the root
PACKAGE_ROOT = '_root_'
# a list of special packages
ALL_PACKAGE_DIRECTIVES = {PACKAGE_GROUP, PACKAGE_ROOT}
# packages are all separated by "." in the name


# ========================================================================= #
# Eunomia Option Keys                                                       #
# ========================================================================= #


def assert_valid_eunomia_key(key: Any) -> str:
    # check the types, that the key is a valid identifier,
    # and that it does not conflict with python.
    if not isinstance(key, str):
        raise TypeError(f'keys must be strings: {repr(key)}')
    if not str.isidentifier(key):
        raise ValueError(f'keys must be valid identifiers: {repr(key)}')
    if keyword.iskeyword(key):
        raise ValueError(f'keys cannot be python keywords: {repr(key)}')

    # check that the key does not conflict with any eunomia reserved keywords
    # and that they key is not "private"
    # if key in KEYS_RESERVED_EUNOMIA:
    #     raise ValueError(f'keys cannot be a eunomia reserved word: {repr(key)}')

    if key in ALL_PACKAGE_DIRECTIVES:
        raise ValueError(f'key is a special package directive and is not allowed: {repr(key)}')
    if key in KEYS_NOT_ALLOWED:
        raise ValueError(f'key is not allowed: {repr(key)}')

    # done!
    return key


def is_valid_eunomia_key(key: Any) -> bool:
    try:
        assert_valid_eunomia_key(key)
        return True
    except:
        return False


# ========================================================================= #
# Eunomia Packages                                                          #
# ========================================================================= #


def _assert_valid_eunomia_keys(keys: Union[str, list, tuple], is_path=False):
    # get info about what kind of keys are being analyzed
    kind, split_char = ('path', '/') if is_path else ('package', '.')

    if isinstance(keys, str):
        keys = keys.split(split_char)
    if not isinstance(keys, (list, tuple)):
        raise TypeError(f'{kind} must be a str, list[str] or tuple[str]')
    if not keys:
        raise ValueError(f'{kind} name must contain at least one group name')

    # can only be a special package
    # directive if the length is one
    if not is_path:
        if len(keys) == 1:
            if keys[0] in ALL_PACKAGE_DIRECTIVES:
                return

    # test all keys in the package
    for key in keys:
        if key in ALL_PACKAGE_DIRECTIVES:
            raise ValueError(f'{kind}: {repr(split_char.join(keys))} group name is package directive: {repr(key)}')
        if key in ALL_RESERVED_KEYS:
            raise ValueError(f'{kind}: {repr(split_char.join(keys))} group name is a reserved key: {repr(key)}')
        try:
            assert_valid_eunomia_key(key)
        except:
            raise ValueError(f'{kind}: {repr(split_char.join(keys))} has invalid group name: {repr(key)}')


def assert_valid_eunomia_package(package: Union[str, list, tuple]):
    return _assert_valid_eunomia_keys(package, is_path=False)


def is_valid_eunomia_package(package: Union[str, list, tuple]):
    try:
        assert_valid_eunomia_package(package)
        return True
    except:
        return False


# ========================================================================= #
# Paths                                                                     #
# ========================================================================= #


def assert_valid_eunomia_path(path: Union[str, list, tuple]):
    return _assert_valid_eunomia_keys(path, is_path=True)


def is_valid_eunomia_path(path: Union[str, list, tuple]):
    try:
        assert_valid_eunomia_path(path)
        return True
    except:
        return False


# ========================================================================= #
# End                                                                       #
# ========================================================================= #



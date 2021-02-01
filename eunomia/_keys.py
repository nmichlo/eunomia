import keyword
from typing import Any, Union, NoReturn


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

PACKAGE_GROUP = '_group_'  # make current option package equal to the path for the group it is in
PACKAGE_ROOT = '_root_'    # makes the current option package the root
# which of the above is the default
PACKAGE_DEFAULT = PACKAGE_GROUP
# a list of special packages
ALL_PACKAGE_DIRECTIVES = {PACKAGE_GROUP, PACKAGE_ROOT}
# packages are all separated by "." in the name

# separators
SEP_PATHS = '/'
SEP_PACKAGES = '.'


# ========================================================================= #
# Eunomia Option Keys                                                       #
# ========================================================================= #


def assert_valid_eunomia_key(key: Any) -> NoReturn:
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


def is_valid_eunomia_key(key: Any) -> bool:
    try:
        assert_valid_eunomia_key(key)
        return True
    except:
        return False


# ========================================================================= #
# Eunomia Packages                                                          #
# ========================================================================= #


def _split_keys(keys: Union[str, list, tuple], is_path: bool):
    # perform checks!
    if isinstance(keys, str):
        keys = keys.split(SEP_PATHS if is_path else SEP_PACKAGES)
    if not isinstance(keys, (list, tuple)):
        raise TypeError(f'{"path" if is_path else "package"}: must be a str, list[str] or tuple[str]')
    if not keys:
        raise ValueError(f'{"path" if is_path else "package"}: name must contain at least one group name')
    # done
    return keys


def _split_and_assert_valid_eunomia_keys(keys: Union[str, list, tuple], is_path: bool) -> list[str]:
    keys = _split_keys(keys, is_path=is_path)

    # can only be a special package
    # directive if the length is one
    if not is_path:
        if len(keys) == 1:
            if keys[0] in ALL_PACKAGE_DIRECTIVES:
                return keys

    # test all keys in the package
    for key in keys:
        if key in ALL_PACKAGE_DIRECTIVES:
            raise ValueError(f'{"path" if is_path else "package"}: {repr(keys)} group name is package directive: {repr(key)}')
        if key in ALL_RESERVED_KEYS:
            raise ValueError(f'{"path" if is_path else "package"}: {repr(keys)} group name is a reserved key: {repr(key)}')
        try:
            assert_valid_eunomia_key(key)
        except Exception as e:
            raise e.__class__(f'{"path" if is_path else "package"}: {repr(keys)} has invalid group name: {repr(key)}\n{e}')

    return keys


def assert_valid_eunomia_package(package: Union[str, list, tuple]) -> NoReturn:
    """
    Checks if a value path listed in the _package_ node of a
    config group option is valid.
    - paths are separated by "."
    - a singular package directive can be used: _root_ or _group_
    """
    split_eunomia_package(package)


def is_valid_eunomia_package(package: Union[str, list, tuple]) -> bool:
    try:
        split_eunomia_package(package)
        return True
    except:
        return False


def split_eunomia_package(package: Union[str, list, tuple]) -> list[str]:
    return _split_and_assert_valid_eunomia_keys(package, is_path=False)


def join_eunomia_package(*keys: str):
    package = SEP_PACKAGES.join(keys)
    assert_valid_eunomia_path(package)
    return package


# ========================================================================= #
# Paths                                                                     #
# ========================================================================= #


def assert_valid_eunomia_path(path: Union[str, list, tuple]) -> NoReturn:
    """
    Checks if a path to a config group or config group option
    is valid.
    - paths are separated by "/"
    - does not allow package directives to be used, otherwise
      the same as assert_valid_eunomia_package
    """
    split_eunomia_path(path)


def is_valid_eunomia_path(path: Union[str, list, tuple]) -> bool:
    try:
        split_eunomia_path(path)
        return True
    except:
        return False


def split_eunomia_path(path: Union[str, list, tuple]) -> list[str]:
    return _split_and_assert_valid_eunomia_keys(path, is_path=True)


def join_eunomia_path(*keys: str):
    path = SEP_PATHS.join(keys)
    assert_valid_eunomia_path(path)
    return path


# ========================================================================= #
# End                                                                       #
# ========================================================================= #



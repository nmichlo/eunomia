import keyword
from typing import Union, Sequence


# ========================================================================= #
# KEY: Single Eunomia Key                                                   #
# ========================================================================= #


class _BaseKey(object):

    def __init__(self, key: Union[str, '_BaseKey']):
        super().__init__()
        # copy if a Key
        if isinstance(key, _BaseKey):
            key = key._key
        if not isinstance(key, str):
            raise TypeError(f'key: {repr(key)} must be a string or {self.__class__.__name__}')
        self._key = key
        self._assert_valid()

    @property
    def key(self):
        return self._key

    def _assert_valid(self):
        # check the types, that the key is a valid identifier,
        # and that it does not conflict with python.
        if not isinstance(self._key, str):
            raise TypeError(f'keys must be strings: {repr(self._key)}')
        if not str.isidentifier(self._key):
            raise ValueError(f'keys must be valid python identifiers: {repr(self._key)}')
        if keyword.iskeyword(self._key):
            raise ValueError(f'keys cannot be python keywords: {repr(self._key)}')

    def __str__(self):
        return self._key

    def __repr__(self):
        return 'k' + repr(self._key)
        # return f'{self.__class__.__name__}({repr(self._key)})'

    def __eq__(self, other):
        if isinstance(other, str):
            return self._key == other
        if isinstance(other, _BaseKey):
            return self._key == other._key
        return False

    def __hash__(self):
        return hash(self._key)


class Key(_BaseKey):
    RESERVED_SET = {}
    RESERVED_MESSAGE = 'key has been reserved'

    # TODO: maybe lift these limitations? They are very restrictive. "keys", "items"
    #       & "values" are popular names. Also package directives names could be useful.
    _KEYS_NOT_ALLOWED = {*dir(dict)}

    def _assert_valid(self):
        super()._assert_valid()
        # check that we do not conflict with reserved keys
        if self._key in PkgPath.PKG_MAP_ALIAS_TO_PATH_FUNC:
            raise ValueError(f'key is a special package alias and is not allowed: {repr(self._key)}')
        if self._key in self._KEYS_NOT_ALLOWED:
            raise ValueError(f'key is not allowed: {repr(self._key)}')
        # reserved keys for this class
        if self._key in self.RESERVED_SET:
            raise ValueError(f'{self.RESERVED_MESSAGE}: {repr(self._key)}')


# ========================================================================= #
# KEYS: Joined Eunomia Keys                                                 #
# ========================================================================= #


class Path(object):

    _KEY_TYPE = Key
    _ALLOW_ROOT = False
    SEP_CHAR = '.'

    def __init__(self, keys: Union[str, 'Path', Sequence[str], Sequence[_BaseKey]]):
        # copy if a Keys object
        if isinstance(keys, Path):
            keys = keys._keys
        # split if a string
        if isinstance(keys, str):
            keys = keys.split(self.SEP_CHAR) if keys else []
        # check that keys is a sequence
        if not isinstance(keys, Sequence):
            raise TypeError('keys must be Sequence')
        # convert to individual keys
        self._keys = tuple(self._KEY_TYPE(key) for key in keys)
        self._assert_valid()

    @property
    def keys(self):
        return tuple(self._keys)

    @property
    def path(self):
        return self.SEP_CHAR.join(key.key for key in self._keys)

    def _assert_valid(self):
        if not self._ALLOW_ROOT:
            if not self._keys:
                raise ValueError(f'Empty path for to root is not allowed: {repr(self)}')

    def __str__(self):
        return self.path

    def __repr__(self):
        return 'p' + repr(self.path)
        # return f'{self.__class__.__name__}({repr(self.path)})'

    def __eq__(self, other):
        if isinstance(other, str):
            return self.path == other
        elif isinstance(other, Sequence):
            return self._keys == tuple(other)
        elif isinstance(other, Path):
            return self._keys == other._keys
        return False

    def __hash__(self):
        return hash(self.path)


# ========================================================================= #
# Single Keys                                                               #
# ========================================================================= #


KEY_GROUP   = '_group_'    # used for dictionaries to indicate that they are a group
KEY_PACKAGE = '_package_'  # options node name to change the current package
KEY_OPTIONS = '_options_'  # options node name to choose the option in a subgroup
KEY_PLUGINS = '_plugins_'  # options node name to choose and adjust various settings for plugins

KEYS_RESERVED_ALL = {
    KEY_GROUP,
    KEY_PACKAGE,
    KEY_OPTIONS,
    KEY_PLUGINS,
}


class InsideOptionKey(Key):
    RESERVED_MESSAGE = 'key reserved for inside groups is not allowed in an option'
    RESERVED_SET = {
        KEY_GROUP,
    }


class InsideGroupKey(Key):
    RESERVED_MESSAGE = 'key reserved for inside options is not allowed in an group'
    RESERVED_SET = {
        KEY_PACKAGE,
        KEY_OPTIONS,
        KEY_PLUGINS,
    }


class GroupKey(Key):
    RESERVED_MESSAGE = 'key reserved for options or groups is not allowed as a path key'
    RESERVED_SET = set(KEYS_RESERVED_ALL)


class PkgKey(Key):
    RESERVED_MESSAGE = 'key reserved for options or groups is not allowed as a package key'
    RESERVED_SET = set(KEYS_RESERVED_ALL)


# ========================================================================= #
# Joined Keys                                                               #
# ========================================================================= #


class GroupPath(Path):
    _KEY_TYPE = GroupKey
    _ALLOW_ROOT = True
    SEP_CHAR = '/'


class PkgPath(Path):
    # override
    _KEY_TYPE = PkgKey
    _ALLOW_ROOT = True
    SEP_CHAR = '.'

    @classmethod
    def try_from_alias(cls, value: str, option: 'ConfigOption'):
        if isinstance(value, str):
            if value in cls.PKG_MAP_ALIAS_TO_PATH_FUNC:
                func = cls.PKG_MAP_ALIAS_TO_PATH_FUNC[value]
                value = func(option)
        return PkgPath(value)

    # values
    PKG_ALIAS_GROUP: str = '_group_'          # make current option package equal to the path for the group it is in
    PKG_ALIAS_ROOT: str = '_root_'            # makes the current option package the root
    PKG_DEFAULT_ALIAS: str = PKG_ALIAS_GROUP  # which of the above is the default

    # A list of special packages:
    #   !! these should only be allowed as the values for
    #      the KEY_PACKAGE key, not as keys themselves
    PKG_MAP_ALIAS_TO_PATH_FUNC: dict = {
        PKG_ALIAS_GROUP: lambda option: option.group_path.keys,
        PKG_ALIAS_ROOT: lambda option: [],
    }


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

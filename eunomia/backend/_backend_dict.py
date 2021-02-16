from eunomia.backend import Backend
from eunomia.config import Group, Option

from eunomia.config import keys as K
from eunomia.config import validate as V


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class BackendDict(Backend):

    GROUP_TYPE = dict
    OPTION_TYPE = dict

    def _load_group(self, value) -> Group:
        # loads below also normalise
        value = normalise_group_dict(value, recursive=False)
        group = Group()
        for key, child in value[K.KEY_CHILDREN].items():
            if child[K.KEY_TYPE] == K.TYPE_GROUP:
                group.add_subgroup(key, self.load_group(child))
            elif child[K.KEY_TYPE] == K.TYPE_OPTION:
                group.add_option(key, self.load_option(child))
            else:
                raise ValueError(f'Invalid type: {child[K.KEY_TYPE]}')
        return group

    def _load_option(cls, value) -> Option:
        # TODO: this should be recursive
        value = normalise_option_dict(value, recursive=False, allow_compact=False)
        return Option(
            pkg=value[K.KEY_PKG],
            defaults=value[K.KEY_DEFAULTS],
            data=value[K.KEY_DATA],
        )

    def _dump_group(self, group: Group):
        group = {
            K.KEY_TYPE: K.TYPE_GROUP,
            K.KEY_CHILDREN: {
                k: self.dump(child)
                for k, child in group._children.items()
            }
        }
        # dump normalises above
        return normalise_group_dict(group, recursive=False)

    def _dump_option(self, option: Option):
        option = {
            K.KEY_TYPE: K.TYPE_OPTION,
            K.KEY_PKG: option._pkg,
            K.KEY_DEFAULTS: option._defaults,
            K.KEY_DATA: option._data,
        }
        # TODO: this should be recursive
        return normalise_option_dict(option, recursive=False, allow_compact=False)


# ========================================================================= #
# VERBOSE VERSIONS                                                          #
# - these versions are used internally                                      #
# ========================================================================= #


def normalise_group_dict(group: dict, recursive: bool):
    assert not recursive, 'recursive normalise is not supported'  # does not validate children
    if not isinstance(group, dict):
        raise TypeError('group must be a dictionary')
    # ========================= #
    # check the keys
    keys = set(group.keys()) - K.RESERVED_GROUP_KEYS
    if keys:
        raise ValueError(f'keys not allowed found in the group: {keys} only these keys are allowed: {K.RESERVED_GROUP_KEYS}')
    # ========================= #
    # set defaults
    type = group.setdefault(K.KEY_TYPE, K.TYPE_GROUP)
    children = group.setdefault(K.KEY_CHILDREN, {})
    # ========================= #
    # validate values
    if not (type == K.TYPE_GROUP):
        raise ValueError(f'group {repr(K.KEY_TYPE)} must be: {repr(K.TYPE_GROUP)}')
    if not isinstance(children, dict):
        raise TypeError(f'group {repr(K.KEY_CHILDREN)} must be of type: {dict}')
    # ========================= #
    return group


def normalise_option_dict(option: dict, recursive: bool, allow_compact=False):
    assert not recursive, 'recursive normalise is not supported'  # does not validate defaults or data
    if not isinstance(option, dict):
        raise TypeError('option must be a dictionary')
    # ========================= #
    # set defaults
    type = option.setdefault(K.KEY_TYPE, K.TYPE_OPTION)
    package = option.setdefault(K.KEY_PKG, K.DEFAULT_PKG)
    defaults = option.setdefault(K.KEY_DEFAULTS, [])
    # ========================= #
    # handle data
    if K.KEY_DATA in option:
        # VERBOSE
        data = option[K.KEY_DATA]
        check_keys = option.keys()
    else:
        if not allow_compact:
            raise KeyError(f'compact options are not allowed, option requires key: {K.KEY_DATA}')
        # COMPACT
        data = option
        data.pop(K.KEY_TYPE)
        data.pop(K.KEY_PKG)
        data.pop(K.KEY_DEFAULTS)
        # check that we have nothing extra
        if any(k in K.RESERVED_KEYS for k in option.keys()):
            raise KeyError(f'A reserved key was found in a compact option dictionary: {list(k for k in option.keys() if k in K.RESERVED_KEYS)}')
        # construct verbose dict
        option = {
            K.KEY_TYPE: type,
            K.KEY_PKG: package,
            K.KEY_DEFAULTS: defaults,
            K.KEY_DATA: data,
        }
        # check keys
        check_keys = data.keys()
    # ========================= #
    # check the keys
    keys = set.intersection(set(check_keys), K.RESERVED_KEYS) - K.RESERVED_OPTION_KEYS
    if keys:
        raise ValueError(f'not allowed reserved keys found in the option: {keys} only the following keys are allowed: {K.RESERVED_OPTION_KEYS}')
    # ========================= #
    # checks
    if not (type == K.TYPE_OPTION):
        raise ValueError(f'option {repr(K.KEY_TYPE)} must be: {repr(K.TYPE_OPTION)}')
    try:
        package = V.validate_package_path(package)
    except:
        raise ValueError(f'option {repr(K.KEY_PKG)} is invalid: {repr(package)}')
    try:
        defaults = V.split_defaults_list_items(defaults, allow_config_node_return=True)
    except:
        raise ValueError(f'option {repr(K.KEY_DEFAULTS)} is invalid: {repr(defaults)}')
    if not isinstance(data, dict):
        raise TypeError(f'option {repr(K.KEY_DATA)} must be of type: {dict}')
    try:
        data = V.validate_config_data(data)
    except:
        raise ValueError(f'data {repr(K.KEY_DATA)} is invalid')
    # ========================= #
    return option


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

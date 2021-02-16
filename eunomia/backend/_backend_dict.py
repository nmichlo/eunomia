from eunomia.backend import Backend
from eunomia.config import Group, Option

from eunomia.config import keys as K
from eunomia.config import validate as V


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #
from eunomia.config.nodes import ConfigNode


class BackendDict(Backend):

    GROUP_TYPE = dict
    OPTION_TYPE = dict

    def __init__(self, allow_compact_load=False):
        self._allow_compact_load = allow_compact_load

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

    def _load_option(self, value) -> Option:
        # TODO: this should be recursive
        value = normalise_option_dict(value, allow_compact=self._allow_compact_load)
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
            K.KEY_PKG: option.pkg,
            K.KEY_DEFAULTS: option.defaults,
            K.KEY_DATA: option.data,
        }
        # TODO: this should be recursive
        return normalise_option_dict(option, allow_compact=False)


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


def normalise_option_dict(option: dict, allow_compact=False, allow_config_nodes=False):
    if not isinstance(option, dict):
        raise TypeError('option must be a dictionary')
    # ========================= #
    # handle compact dictionary -- identified if extra keys exist
    extra_keys = set(option.keys()) - K.RESERVED_OPTION_KEYS
    if extra_keys:
        # COMPACT
        if not allow_compact:
            raise KeyError(f'compact options are not allowed, option requires key: {K.KEY_DATA}')
        if K.KEY_DATA in option:
            raise ValueError(f'option is considered compact because it has extra non-special keys in it. A compact option cannot contain a {K.KEY_DATA} key itself.')
        option = {
            K.KEY_TYPE:     option.pop(K.KEY_TYPE, None),
            K.KEY_PKG:      option.pop(K.KEY_PKG, None),
            K.KEY_DEFAULTS: option.pop(K.KEY_DEFAULTS, None),
            K.KEY_DATA:     option,
        }
    # ========================= #
    # get defaults
    option[K.KEY_TYPE]     = V.validate_option_type(option.get(K.KEY_TYPE, None))
    option[K.KEY_PKG]      = V.validate_option_package(option.get(K.KEY_PKG, None))
    option[K.KEY_DEFAULTS] = V.validate_option_defaults(option.get(K.KEY_DEFAULTS, None), allow_config_nodes=allow_config_nodes)
    option[K.KEY_DATA]     = V.validate_option_data(option.get(K.KEY_DATA, None))
    # ========================= #
    # again check that no extra keys exist
    extra_keys = set(option.keys()) - K.RESERVED_OPTION_KEYS
    if extra_keys:
        raise ValueError(f'option has extra keys that are not allowed: {extra_keys}')
    # check that nothing special is in here
    extra_data_keys = set(option[K.KEY_DATA].keys()).intersection(K.RESERVED_KEYS)
    if extra_data_keys:
        raise ValueError(f'option data has reserved keys that are not allowed: {extra_data_keys}')
    # ========================= #
    return option


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

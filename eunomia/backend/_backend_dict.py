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


# def _update_option_overrides(option, data=None, pkg=None, defaults=None, allow_compact=False):
#     if pkg is not None:
#         if K.KEY_PKG in option:
#             raise ValueError(f'package parameter cannot be specified if {K.KEY_PKG} is in the option')
#         option[K.KEY_PKG] = pkg
#     if data is not None:
#         if K.KEY_DATA in option:
#             raise ValueError(f'data parameter cannot be specified if {K.KEY_DATA} is in the option')
#         if allow_compact and (set(option.keys()) - K.RESERVED_OPTION_KEYS):
#             raise ValueError(f'data parameter cannot be specified if the compact mode is being used and there are data keys.')
#         option[K.KEY_DATA] = data
#     if defaults is not None:
#         if K.KEY_DEFAULTS in option:
#             raise ValueError(f'defaults parameter cannot be specified if {K.KEY_DEFAULTS} is in the option')
#         option[K.KEY_DEFAULTS] = defaults
#     return option


def _set_option_defaults_and_normalise(option, allow_compact=False):
    # ========================= #
    # set defaults
    option.setdefault(K.KEY_TYPE, K.TYPE_OPTION)
    option.setdefault(K.KEY_PKG, None)
    option.setdefault(K.KEY_DEFAULTS, None)
    # ========================= #
    # handle data
    if not (set(option.keys()) - K.RESERVED_OPTION_KEYS):
        # VERBOSE
        option.setdefault(K.KEY_DATA, None)
        check_keys = option.keys()
    else:
        if not allow_compact:
            raise KeyError(f'compact options are not allowed, option requires key: {K.KEY_DATA}')
        # COMPACT
        data = option
        type = data.pop(K.KEY_TYPE)
        package = data.pop(K.KEY_PKG)
        defaults = data.pop(K.KEY_DEFAULTS)
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
    return option


def _validate_option_keys(option, allow_config_nodes=False):
    typ, pkg, defaults, data = option[K.KEY_TYPE], option[K.KEY_PKG], option[K.KEY_DEFAULTS], option[K.KEY_DATA]
    # ========================= #
    # type
    if isinstance(typ, ConfigNode):
        raise RuntimeError(f'option type can never be a config node: {repr(typ)}')
    if typ != K.TYPE_OPTION:
        raise RuntimeError(f'option  type must be: {repr(typ)}')
    # ========================= #
    # package
    option[K.KEY_PKG] = V.validate_option_package(pkg)
    option[K.KEY_DEFAULTS] = V.validate_option_defaults(defaults, allow_config_nodes=allow_config_nodes)
    option[K.KEY_DATA] = V.validate_option_data(data)
    # ========================= #
    return option


def normalise_option_dict(option: dict, allow_compact=False, allow_config_nodes=False):
    if not isinstance(option, dict):
        raise TypeError('option must be a dictionary')
    # ========================= #
    option = _set_option_defaults_and_normalise(option, allow_compact=allow_compact)
    option = _validate_option_keys(option, allow_config_nodes=allow_config_nodes)
    # ========================= #
    return option


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

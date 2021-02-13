from typing import Iterable, Tuple
from eunomia.config import Option
from eunomia.config import scheme as s
from eunomia.backend import Backend
from eunomia.config.nodes import ConfigNode


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def recursive_getitem(dct, keys: Iterable[str], make_missing=False):
    if not keys:
        return dct
    (key, *keys) = keys
    if make_missing:
        if key not in dct:
            dct[key] = {}
    return recursive_getitem(dct[key], keys, make_missing=make_missing)


def recursive_setitem(dct, keys: Iterable[str], value, make_missing=False):
    (key, *keys) = keys
    insert_at = recursive_getitem(dct, keys, make_missing=make_missing)
    insert_at[key] = value


def _dict_recursive_update(left, right, stack):
    # right overwrites left
    for k, v in right.items():
        if k in left:
            if isinstance(left[k], dict) or isinstance(v, dict):
                new_stack = stack + [k]
                if not (isinstance(left[k], dict) and isinstance(v, dict)):
                    raise TypeError(f'Recursive update cannot merge keys with a different type if one is a dictionary. {".".join(new_stack)}')
                else:
                    _dict_recursive_update(left[k], v, stack=new_stack)
                    continue
        left[k] = v


def dict_recursive_update(left, right):
    _dict_recursive_update(left, right, [])


# ========================================================================= #
# Config Loader                                                             #
# ========================================================================= #


class ConfigLoader(object):

    def __init__(self, storage_backend: Backend):
        self._backend = storage_backend
        # merged items
        self._merged_options = None
        self._merged_config = None

    def load_config(self, config_name, return_merged_options=False):
        """
        flatten and merge the options lists using DFS, while
        simultaneously merging the config

        - When config dictionaries are encountered, those are also
          processed using DFS to obtain substituted values, before
          being merged into the config.
            * Keys are not allowed to be substituted values
        """
        self._merged_options = {}
        self._merged_config = {}

        # ===================== #
        # 1. entry point for dfs, get initial option
        root_group = self._backend.load_root_group()
        entry_option = root_group.get_option(config_name)
        # ===================== #
        # 2. perform dfs & merging and finally resolve values
        self._visit_option(entry_option)
        # ===================== #
        # 3. finally resolve all the values in the config
        self._resolve_all_values()
        # ===================== #

        # done, return the result
        if return_merged_options:
            return self._merged_config, self._merged_options
        return self._merged_config

    def _visit_option(self, option: Option):
        # ===================== #
        # 1. check where to process self, and make sure self is in the options list
        # by default we want to merge this before children so we can reference its values.
        options = option.get_unresolved_includes()
        group_paths = list(options.keys())
        if s.OPT_SELF not in group_paths:
            # allow referencing parent values in children
            group_paths = [s.OPT_SELF] + group_paths
            # # allow parent overwriting children values
            # group_paths = group_paths + [s.OPT_SELF]
        # ===================== #
        # 2. process options in order
        for group_path in group_paths:
            # handle different cases
            if group_path == s.OPT_SELF:
                # ===================== #
                # 2.a if self is encountered, merge into config. We skip the
                #     value of the option_name here as it is not needed.
                self._merge_option(option)
                # ===================== #
            else:
                # get the option name and resolve
                option_name = options[group_path]
                option_name = self._resolve_value(option_name)
                # ===================== #
                # 2.b dfs through options
                # supports relative & absolute paths
                group = option.group.get_group_from_path(group_path, make_missing=False)
                # visit the next option
                self._visit_option(group.get_option(option_name))
                # ===================== #

    def _merge_option(self, option: Option):
        # 1. check that the group has not already been merged
        # 2. check that the option has not already been merged
        self._merge_option_mark_visited(option)
        # 3. merged the data
        self._merge_option_into_config(option)

    def _merge_option_mark_visited(self, option: Option):
        # TODO: this should have different modes
        #       - do not allow from the same group to be merged
        #       - allow from the same group to be merged
        #       1. check that the group has not already been merged
        #       2. check that the option has not already been merged
        # get the path to the config - recursive version of whats listed in the __include__
        # maybe lift the non-recursive limitation in future?
        group_keys = option.group_keys
        # check that this is not a duplicate
        if group_keys in self._merged_options:
            prev_added_keys = self._merged_options[group_keys]
            raise KeyError(f'Group has duplicate entry: {repr(group_keys)}. '
                           f'Key previously added by: {repr(prev_added_keys)}. '
                           f'Current config file is: {repr(option.keys)}.')
        # merge the path!
        self._merged_options[group_keys] = option.keys

    def _merge_option_into_config(self, option: Option):
        # 1. get the package and handle special values
        keys = self._resolve_package(option)
        # 2. get the root config object according to the package
        root = recursive_getitem(self._merged_config, keys, make_missing=True)
        # 3. merge the option into the config
        dict_recursive_update(left=root, right=option.get_unresolved_data())

    def _resolve_value(self, value):
        # 1. allow interpolation of config objects
        # 2. process dictionary syntax with _node_ keys
        if isinstance(value, ConfigNode):
            value = value.get_config_value(self._merged_config, self._merged_options, {})
        if isinstance(value, dict):
            if s.KEY_NODE in value:
                raise RuntimeError(f'{s.KEY_NODE} is not yet supported!')
        return value

    def _resolve_package(self, option) -> Tuple[str]:
        path = self._resolve_value(option.get_unresolved_package())
        # check the type
        if not isinstance(path, str):
            raise TypeError(f'{s.KEY_PKG} must be a string')
        # handle special values
        if path == s.PKG_ROOT:
            keys = ()
        elif path == s.PKG_GROUP:
            keys = option.group_keys
        else:
            keys, is_relative = s.split_pkg_path(path)
            if is_relative:
                keys = option.group_keys + keys
        # return the keys
        return keys

    def _resolve_all_values(self):
        # TODO: this is wrong!
        # TODO: config is not mutated on the fly, cannot substitute chains of values.
        self._merged_config = ConfigNode.recursive_get_config_value(
            self._merged_config,
            self._merged_options,
            {},
            self._merged_config
        )


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

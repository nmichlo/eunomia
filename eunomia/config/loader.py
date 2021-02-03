from typing import Iterable
from eunomia.values import BaseValue
from eunomia.backend import Backend
from eunomia.config._objects import ConfigOption, ConfigGroup
from eunomia.values._values import recursive_get_config_value


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

    def load_config(self, config_name, return_merged_options=False):
        """
        flatten and merge the options lists using DFS, while
        simultaneously merging the config

        - When config dictionaries are encountered, those are also
          processed using DFS to obtain interpolated values, before
          being merged into the config.
            * Keys are not allowed to be interpolated values
        """

        merged_options = {}
        merged_config = {}

        def _mark_option_visited(option: ConfigOption):
            # get the path to the config - recursive version of whats listed in the _options_
            # maybe lift the non-recursive limitation in future?
            group_path = option.group_path
            # check that this is not a duplicate
            if group_path in merged_options:
                prev_added_path = merged_options[group_path]
                raise KeyError(f'Group has duplicate entry: {repr(group_path)}. '
                               f'Key previously added by: {repr(prev_added_path)}. '
                               f'Current config file is: {repr(option.path)}.')
            # merge the path!
            merged_options[group_path] = option.path

        def _merge_config_values(option: ConfigOption):
            # This function needs to do two things
            # 1. recursively merge the option config into the merged config
            # 2. recursively interpolate encountered values
            # get and make directories in the config according to the package
            package = option.resolve_package(merged_config, merged_options, {})
            left = recursive_getitem(merged_config, package.keys, make_missing=True)
            # get the actual option to merge
            right = option.config
            # perform the merge
            dict_recursive_update(left=left, right=right)

        def _resolve_value(value):
            if isinstance(value, BaseValue):
                value = value.get_config_value(merged_config, merged_options, {})
            return value

        def _dfs_option(option: ConfigOption):
            assert isinstance(option, ConfigOption)
            group = option.parent
            assert isinstance(group, ConfigGroup)
            # process all sub_groups
            for subgroup_key, suboption_key in option.options.items():
                subgroup = group.get_subgroup(subgroup_key)
                suboption = subgroup.get_option(_resolve_value(suboption_key))
                _handle_option(suboption)

        def _handle_option(option: ConfigOption):
            # TODO: add _plugins_ support
            _mark_option_visited(option)
            _merge_config_values(option)
            _dfs_option(option)

        # entry point for dfs
        root_group = self._backend.load_root_group()
        entry_option = root_group.get_option(config_name)

        # perform dfs & merging and finally resolve values
        _handle_option(entry_option)
        # TODO: this is incorrect
        merged_config = recursive_get_config_value(merged_config, merged_options, {}, value=merged_config)

        # done, return the result
        if return_merged_options:
            return merged_config, merged_options
        return merged_config


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

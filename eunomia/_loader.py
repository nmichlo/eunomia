from typing import Iterator
from eunomia.backend import Backend, ConfigOption, ConfigGroup


# ========================================================================= #
# Config Loaders                                                            #
# ========================================================================= #


class ConfigLoader(object):

    def __init__(self, storage_backend: Backend):
        self._backend = storage_backend

    def _traverse(self, entrypoint: str) -> Iterator[ConfigOption]:
        def _dfs(group: ConfigGroup, option_key: str):
            option = group.get_option(option_key)
            # yield the values
            yield option
            # append all the defaults contained in the subconfig to the stack
            for subgroup_key, suboption_key in option.options.items():
                yield from _dfs(
                    group=group.get_subgroup(subgroup_key),
                    option_key=suboption_key,
                )
        yield from _dfs(self._backend.load_root_group(), entrypoint)

    def load_config(self, config_name, return_merged_options=False):
        merged_options = {}
        merged_config = {}

        # flatten and merge the defaults list using DFS, while
        # simultaneously merging the config
        for option in self._traverse(config_name):
            # get the path to the config - recursive version of whats listed in the _options_
            # maybe lift the non-recursive limitation in future?
            group_path = option.parent.path
            # check that this is not a duplicate
            if group_path in merged_options:
                prev_added_opt: ConfigOption = merged_options[group_path]
                raise KeyError(f'Group has duplicate entry: {repr(group_path)}. '
                               f'Key previously added by: {repr(prev_added_opt.path)}. '
                               f'Current config file is: {repr(option.path)}.')
            # 1. merge the defaults!
            merged_options[group_path] = option
            # 2. second recursively merge the configs
            # TODO: add resolving of variables
            # TODO: add _package_ support
            # TODO: add _plugins_ support
            _recursive_update_dict(merged_config, option.config)

        if return_merged_options:
            return merged_config, merged_options
        else:
            return merged_config


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def _recursive_update_dict(left, right, stack=None):
    if stack is None:
        stack = []
    # b takes priority
    for k, v in right.items():
        if k in left:
            if isinstance(left[k], dict) or isinstance(v, dict):
                new_stack = stack + [k]
                if not (isinstance(left[k], dict) and isinstance(v, dict)):
                    raise TypeError(f'Recursive update cannot merge keys with a different type if one is a dictionary. {".".join(new_stack)}')
                else:
                    _recursive_update_dict(left[k], v, stack=new_stack)
                    continue
        left[k] = v


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

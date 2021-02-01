import os as os
from typing import NamedTuple, Iterator
from eunomia.backend import Backend


# ========================================================================= #
# Config Loaders                                                            #
# ========================================================================= #


class ConfigLoader(object):

    class ConfigInfo(NamedTuple):
        # values
        config: 'GroupOption'
        # paths
        subgroups: list[str]
        subconfig: str
        parent: str

        def get_defaults_key(self):
            return os.path.join(*self.subgroups) if self.subgroups else None

    def __init__(self, storage_backend: Backend):
        self._backend = storage_backend

    def _traverse(self, config_name) -> Iterator[ConfigInfo]:
        def _dfs(curr_subgroups, curr_subconfig, parent_path):
            # load the current config option in the subgroup
            path = os.path.join(*curr_subgroups, curr_subconfig)
            config = GroupOption(self._get_config_data(path), path)
            # yield the values
            yield ConfigLoader.ConfigInfo(config, curr_subgroups, curr_subconfig, parent_path)
            # append all the defaults contained in the subconfig to the stack
            for subgroup, subconfig in config.defaults.items():
                yield from _dfs(
                    curr_subgroups=curr_subgroups + [subgroup],
                    curr_subconfig=subconfig,
                    parent_path=path
                )
        yield from _dfs([], config_name, None)

    def load_config(self, config_name, simultaneous_merge=True):
        if simultaneous_merge:
            return self._load_config_simultaneous(config_name)
        else:
            return self._load_config_separate(config_name)

    def _load_config_simultaneous(self, config_name):
        merged_defaults = {}
        merged_config = {}

        # flatten and merge the defaults list using DFS, while
        # simultaneously merging the config
        for info in self._traverse(config_name):
            # get the defaults key
            defaults_key = info.get_defaults_key()
            # check that there is not a duplicate
            if defaults_key in merged_defaults:
                prev_info = merged_defaults[defaults_key]
                raise KeyError(f'Merged defaults has duplicate entry: {repr(defaults_key)}. '
                               f'Key previously added by: {repr(info.parent + conf_paths.EXT)}. '
                               f'Current config file is: {repr(prev_info.parent + conf_paths.EXT)}.')
            # 1. merge the defaults!
            merged_defaults[defaults_key] = info
            # 2. second recursively merge the configs
            # TODO: add resolving of variables
            conf_paths.recursive_update(merged_config, info.config.data)

        return merged_config

    def _load_config_separate(self, config_name):
        """
        This is like
        """

        # 1. first flatten and merge the defaults list using DFS
        merged_defaults = {}
        for info in self._traverse(config_name):
            # get the defaults key
            defaults_key = info.get_defaults_key()
            # check that there is not a duplicate
            if defaults_key in merged_defaults:
                prev_info = merged_defaults[defaults_key]
                raise KeyError(f'Merged defaults has duplicate entry: {repr(defaults_key)}. '
                               f'Key previously added by: {repr(info.parent)}. '
                               f'Current config file is: {repr(prev_info.parent)}.')
            # merge the defaults!
            merged_defaults[defaults_key] = info

        # 2. second recursively merge the configs in the merged defaults lists
        merged_config = {}
        for defaults_key, info in merged_defaults.items():
            recursive_update_dict(merged_config, info.config.data)

        return merged_config


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

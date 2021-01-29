import os as os
from typing import NamedTuple, Iterator
from eunomia._yaml import yaml_load_file, yaml_load
from eunomia import _util as util


# ========================================================================= #
# Config                                                                    #
# ========================================================================= #


class Config(object):

    KEY_DEFAULTS = '_defaults_'  # default is {}
    KEY_PACKAGE = '_package_'    # default is _group_

    PACKAGE_GROUP = '_group_'
    PACKAGE_GLOBAL = '_global_'

    def __init__(self, data: dict, key: str):
        self.key = key
        # extract various components from the config
        # TODO: reenable data = replace_interpolators(data)
        self.defaults = self._config_pop_defaults(data)
        self.package = self._config_pop_package(data)
        self.data = data

    def _config_pop_defaults(self, data: dict) -> dict:
        # split the config file
        defaults = data.pop(Config.KEY_DEFAULTS, {})
        # hydra support for defaults that are lists of pairs
        if isinstance(defaults, list):
            new_defaults = {k: v for k, v in defaults}
            assert len(new_defaults) == len(
                defaults), f'Config file: {self.key=} ERROR: keys in defaults are not unique (deprecated hydra support for lists)'
            defaults = new_defaults
        # check types
        assert isinstance(defaults, dict), f'Config: {self.key=} ERROR: defaults must be a mapping!'
        return defaults

    def _config_pop_package(self, data: dict) -> str:
        package = data.pop(Config.KEY_DEFAULTS, Config.PACKAGE_GROUP)
        assert isinstance(package, str), f'Config: {self.key=} ERROR: package must be a string!'
        return package


# ========================================================================= #
# Config Loaders                                                            #
# ========================================================================= #


class ConfigLoader(object):

    class ConfigInfo(NamedTuple):
        # values
        config: Config
        # paths
        subgroups: list[str]
        subconfig: str
        parent: str

        def get_defaults_key(self):
            return os.path.join(*self.subgroups) if self.subgroups else None

    def _traverse(self, config_name) -> Iterator[ConfigInfo]:
        def _dfs(curr_subgroups, curr_subconfig, parent_path):
            # load the current config in the subgroup
            path = os.path.join(*curr_subgroups, curr_subconfig)
            config = Config(self._get_config_data(path), path)
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

    def _get_config_data(self, path: str):
        raise NotImplementedError()

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
                               f'Key previously added by: {repr(info.parent + util.EXT)}. '
                               f'Current config file is: {repr(prev_info.parent + util.EXT)}.')
            # 1. merge the defaults!
            merged_defaults[defaults_key] = info
            # 2. second recursively merge the configs
            # TODO: add resolving of variables
            util.recursive_update(merged_config, info.config.data)

        return merged_config

    def _load_config_separate(self, config_name):
        # 1. first flatten and merge the defaults list using DFS
        merged_defaults = {}
        for info in self._traverse(config_name):
            # get the defaults key
            defaults_key = info.get_defaults_key()
            # check that there is not a duplicate
            if defaults_key in merged_defaults:
                prev_info = merged_defaults[defaults_key]
                raise KeyError(f'Merged defaults has duplicate entry: {repr(defaults_key)}. '
                               f'Key previously added by: {repr(info.parent + util.EXT)}. '
                               f'Current config file is: {repr(prev_info.parent + util.EXT)}.')
            # merge the defaults!
            merged_defaults[defaults_key] = info

        # 2. second recursively merge the configs in the merged defaults lists
        merged_config = {}
        for defaults_key, info in merged_defaults.items():
            util.recursive_update(merged_config, info.config.data)

        return merged_config


class DiskConfigLoader(ConfigLoader):

    def __init__(self, config_folder):
        super().__init__()
        self._config_folder = config_folder

    def _get_config_data(self, path: str):
        # load the config file
        disk_path = util.add_extension(os.path.join(self._config_folder, path))
        config = yaml_load_file(disk_path)
        # split the config file
        return config


class DictConfigLoader(ConfigLoader):

    def __init__(self, data: dict):
        super().__init__()
        self._data = data

    def _get_config_data(self, path: str):
        config = util.recursive_get(self._data, util.split_elems(path))
        # TODO: some sort of check that we haven't gone too far into the config.
        #       maybe add group datatype, or config datatype
        # split the config file
        return config


class VirtualConfigLoader(DictConfigLoader):

    def _get_config_data(self, path: str):
        config_string = super()._get_config_data(path)
        return yaml_load(config_string)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

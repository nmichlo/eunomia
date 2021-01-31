import os
from eunomia.backend._yaml import yaml_load, yaml_load_file


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class ConfigBackend(object):

    def _get_config_data(self, keys: list[str]):
        raise NotImplementedError


# ========================================================================= #
# Impl Backend                                                              #
# ========================================================================= #


class DiskConfigLoader(ConfigBackend):

    def __init__(self, config_root):
        super().__init__()
        self._config_folder = config_root

    def _get_config_data(self, keys: list[str]):
        # load the config file
        disk_path = conf_paths.add_extension(os.path.join(self._config_folder, *keys))
        config = yaml_load_file(disk_path)
        # split the config file
        return config


class DictConfigLoader(ConfigBackend):

    def __init__(self, data: dict):
        super().__init__()
        self._data = data

    def _get_config_data(self, keys: list[str]):
        config = conf_paths.recursive_get(self._data, keys)
        # TODO: some sort of check that we haven't gone too far into the config.
        #       maybe add group datatype, or config datatype
        # split the config file
        return config


class VirtualConfigLoader(ConfigBackend):

    def __init__(self, data: dict):
        super().__init__()
        self._data = data

    def _get_config_data(self, keys: list[str]):
        config_string = super()._get_config_data(keys)
        return yaml_load(config_string)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

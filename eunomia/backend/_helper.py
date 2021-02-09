from pathlib import Path
from typing import Union

from eunomia.backend import BackendYaml, BackendDict, BackendObj
from eunomia.config import Group


ValidConfigTypes = Union[str, Path, dict, Group]


def make_backend(config: ValidConfigTypes):
    if isinstance(config, (str, Path)):
        # we assume the config is a path to the root folder for a YAML backend
        if isinstance(config, Path):
            config = str(config.absolute())
        return BackendYaml(root_folder=config)
    elif isinstance(config, dict):
        # we assume that the config is a dictionary
        return BackendDict(root_dict=config)
    elif isinstance(config, Group):
        # we assume that the config is a ConfigGroup with ConfigOptions
        return BackendObj(root_group=config)
    else:
        raise TypeError(f'Unsupported config_root type: {config.__class__.__name__}')

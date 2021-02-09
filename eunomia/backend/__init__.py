from ._backend import Backend
from ._backend_dict import BackendDict
from ._backend_obj import BackendObj
from ._backend_yaml import BackendYaml


from pathlib import Path as _Path
from typing import Union as _Union
from eunomia.config import Group as _Group


ValidConfigTypes = _Union[str, _Path, dict, _Group]


def get_backend(config: ValidConfigTypes):
    if isinstance(config, (str, _Path)):
        # we assume the config is a path to the root folder for a YAML backend
        if isinstance(config, _Path):
            config = str(config.absolute())
        return BackendYaml(root_folder=config)
    elif isinstance(config, dict):
        # we assume that the config is a dictionary
        return BackendDict(root_dict=config)
    elif isinstance(config, _Group):
        # we assume that the config is a ConfigGroup with ConfigOptions
        return BackendObj(root_group=config)
    else:
        raise TypeError(f'Unsupported config_root type: {config.__class__.__name__}')


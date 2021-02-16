from pathlib import Path
from typing import Union

from eunomia.backend import BackendYaml, BackendDict, BackendObj, Backend
from eunomia.config import Group


DefaultConfigTypes = Union[str, Path, dict, Group]


def infer_backend_load_group(config: DefaultConfigTypes, backend: Backend = None) -> Group:
    # override backend
    if backend is not None:
        return backend.load_group(config)
    # infer backend
    if isinstance(config, str):
        return BackendYaml().load_group(config)
    elif isinstance(config, dict):
        # we assume that the config is a dictionary
        return BackendDict().load_group(config)
    elif isinstance(config, Group):
        # we assume that the config is a ConfigGroup with ConfigOptions
        return BackendObj().load_group(config)
    else:
        raise TypeError(f'Unsupported config_root type: {config.__class__.__name__}')

from functools import wraps
import pathlib
from typing import Union

from eunomia._loader import ConfigLoader
from eunomia.backend import Backend, ConfigGroup, BackendConfigGroup, BackendYaml, BackendDict


DEFAULT_CONFIG = 'configs'
DEFAULT_ENTRYPOINT = 'default'

ValidConfigTypes = Union[str, dict, ConfigGroup]


# ========================================================================= #
# Decorators                                                                #
# ========================================================================= #


def eunomia(config: ValidConfigTypes = DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT):
    """
    The main eunomia decorator.
    Automatically detects which backend to use based on the first argument.
    """
    def wrapper(func):
        @wraps(func)
        def runner():
            return eunomia_runner(func=func, config=config, entrypoint=entrypoint)
        return runner
    return wrapper


def eunomia_adv(backend: Backend, entrypoint=DEFAULT_ENTRYPOINT):
    """
    The main eunomia decorator.
    Use this decorator if you want to instantiate the backend manually.
    """
    def wrapper(func):
        @wraps(func)
        def runner():
            return eunomia_runner_adv(func=func, backend=backend, entrypoint=entrypoint)
        return runner
    return wrapper


def eunomia_runner(func: callable, config: ValidConfigTypes = DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT):
    """
    The non-decorator equivalent to @eunomia(...)
    """
    return eunomia_runner_adv(
        func=func,
        backend=_eunomia_get_backend(config),
        entrypoint=entrypoint
    )


def eunomia_runner_adv(func: callable, backend: Backend, entrypoint=DEFAULT_ENTRYPOINT):
    """
    The non-decorator equivalent to @eunomia_adv(...)
    - This function is the core of eunomia, calling the relevant plugins, creating
      the merged config and finally calling your entry.
    """
    raise NotImplementedError


# ========================================================================= #
# Single Config Loading - No Wrapping                                       #
# ========================================================================= #


def eunomia_load(config: ValidConfigTypes = DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT):
    return eunomia_load_adv(
        backend=_eunomia_get_backend(config),
        entrypoint=entrypoint
    )


def eunomia_load_adv(backend: Backend, entrypoint=DEFAULT_ENTRYPOINT):
    loader = ConfigLoader(backend)
    return loader.load_config(entrypoint)


# ========================================================================= #
# Util                                                                      #
# ========================================================================= #


def _eunomia_get_backend(config: ValidConfigTypes = DEFAULT_CONFIG):
    if isinstance(config, (str, pathlib.Path)):
        # we assume the config is a path to the root folder for a YAML backend
        if isinstance(config, pathlib.Path):
            config = str(config.absolute())
        return BackendYaml(root_folder=config)
    elif isinstance(config, dict):
        # we assume that the config is a dictionary
        return BackendDict(root_dict=config)
    elif isinstance(config, ConfigGroup):
        # we assume that the config is a ConfigGroup with ConfigOptions
        return BackendConfigGroup(root_group=config)
    else:
        raise TypeError(f'Unsupported config_root type: {config.__class__.__name__}')


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

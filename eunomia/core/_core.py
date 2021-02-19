from typing import List

from eunomia.config import ConfigLoader
from eunomia.backend import Backend, BackendObj, BackendYaml, BackendDict
from eunomia.backend import ValidConfigTypes, infer_backend_load_group as _infer_backend_load_group
from eunomia.core.runner import RunnerLocal
from eunomia.core.runner._runner import BaseRunner


# ========================================================================= #
# Variables                                                                 #
# ========================================================================= #


# default config gives BackedYaml pointing to ./configs
# default entrypoint recursively loads ./configs/default.yaml

DEFAULT_CONFIG = 'configs'
DEFAULT_ENTRYPOINT = 'default'


# ========================================================================= #
# Decorators                                                                #
# ========================================================================= #


def eunomia(
        config: ValidConfigTypes = DEFAULT_CONFIG,
        entrypoint=DEFAULT_ENTRYPOINT,
        overrides: List = None,
        backend: Backend = None,
        runner: BaseRunner = None,
):
    """
    The main eunomia decorator.
    Automatically detects which backend to use based on the first argument.
    """
    def wrapper(func):
        from functools import wraps
        @wraps(func)
        def wrapper():
            eunomia_runner(func=func, config=config, entrypoint=entrypoint, overrides=overrides, backend=backend, runner=runner)
        return wrapper
    return wrapper


def eunomia_runner(
        func: callable,
        config: ValidConfigTypes = DEFAULT_CONFIG,
        entrypoint=DEFAULT_ENTRYPOINT,
        overrides: List = None,
        backend: Backend = None,
        runner: BaseRunner = None,
):
    """
    The non-decorator equivalent to @eunomia(...)
    - This function is the core of eunomia, calling the relevant plugins, creating
      the merged config and finally calling your entry.
    """
    if runner is None:
        runner = RunnerLocal()
    # run this!
    runner.run(func, config, entrypoint, overrides, backend)


# ========================================================================= #
# Single Config Loading - No Wrapping                                       #
# ========================================================================= #


def eunomia_load(
        config: ValidConfigTypes = DEFAULT_CONFIG,
        entrypoint=DEFAULT_ENTRYPOINT,
        overrides: List = None,
        backend: Backend = None,
) -> dict:
    # this should not allow matrix...
    group = _infer_backend_load_group(config, backend=backend)
    loader = ConfigLoader(group, overrides=overrides)
    return loader.load_config(entrypoint)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

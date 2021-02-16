from eunomia.config import ConfigLoader
from eunomia.backend import Backend, BackendObj, BackendYaml, BackendDict
from eunomia.backend import DefaultConfigTypes as _ValidConfigTypes, infer_backend_load_group as _infer_backend_load_group

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


def eunomia(config: _ValidConfigTypes = DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT, backend: Backend = None):
    """
    The main eunomia decorator.
    Automatically detects which backend to use based on the first argument.
    """
    def wrapper(func):
        from functools import wraps
        @wraps(func)
        def runner():
            return eunomia_runner(func=func, config=config, entrypoint=entrypoint, backend=backend)
        return runner
    return wrapper


def eunomia_runner(func: callable, config: _ValidConfigTypes = DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT, backend: Backend = None):
    """
    The non-decorator equivalent to @eunomia(...)
    - This function is the core of eunomia, calling the relevant plugins, creating
      the merged config and finally calling your entry.
    """
    config = eunomia_load(
        config=config,
        entrypoint=entrypoint,
        backend=backend,
    )
    # TODO: extract runner from config, and run that way!
    func(config)


# ========================================================================= #
# Single Config Loading - No Wrapping                                       #
# ========================================================================= #


def eunomia_load(config: _ValidConfigTypes = DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT, backend: Backend = None):
    group = _infer_backend_load_group(config, backend=backend)
    loader = ConfigLoader(group)
    return loader.load_config(entrypoint)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

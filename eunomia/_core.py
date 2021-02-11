from eunomia.config import ConfigLoader
from eunomia.backend import Backend, BackendObj, BackendYaml, BackendDict
from eunomia.backend import ValidConfigTypes as _ValidConfigTypes, make_backend as _make_backend

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


def eunomia(config: _ValidConfigTypes = DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT):
    """
    The main eunomia decorator.
    Automatically detects which backend to use based on the first argument.
    """
    def wrapper(func):
        from functools import wraps
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
        from functools import wraps
        @wraps(func)
        def runner():
            return eunomia_runner_adv(func=func, backend=backend, entrypoint=entrypoint)
        return runner
    return wrapper


def eunomia_runner(func: callable, config: _ValidConfigTypes = DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT):
    """
    The non-decorator equivalent to @eunomia(...)
    """
    return eunomia_runner_adv(
        func=func,
        backend=_make_backend(config),
        entrypoint=entrypoint
    )


def eunomia_runner_adv(func: callable, backend: Backend, entrypoint=DEFAULT_ENTRYPOINT):
    """
    The non-decorator equivalent to @eunomia_adv(...)
    - This function is the core of eunomia, calling the relevant plugins, creating
      the merged config and finally calling your entry.
    """
    config = eunomia_load_adv(
        backend=backend,
        entrypoint=entrypoint
    )
    # TODO: extract runner from config, and run that way!
    func(config)


# ========================================================================= #
# Single Config Loading - No Wrapping                                       #
# ========================================================================= #


def eunomia_load(config: _ValidConfigTypes = DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT):
    return eunomia_load_adv(
        backend=_make_backend(config),
        entrypoint=entrypoint
    )


def eunomia_load_adv(backend: Backend, entrypoint=DEFAULT_ENTRYPOINT):
    loader = ConfigLoader(backend)
    return loader.load_config(entrypoint)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

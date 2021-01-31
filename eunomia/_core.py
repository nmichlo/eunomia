from functools import wraps
from eunomia._loader import ConfigLoader
from eunomia.backend import ConfigBackend, DiskConfigLoader, DictConfigLoader
import pathlib


DEFAULT_CONFIG = 'configs'
DEFAULT_ENTRYPOINT = 'default'


# ========================================================================= #
# Decorators                                                                #
# ========================================================================= #


def eunomia(config=DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT):
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


def eunomia_adv(backend: ConfigBackend, entrypoint=DEFAULT_ENTRYPOINT):
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


def eunomia_runner(func: callable, config=DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT):
    """
    The non-decorator equivalent to @eunomia(...)
    """
    return eunomia_runner_adv(
        func=func,
        backend=_eunomia_get_backend(config),
        entrypoint=entrypoint
    )


def eunomia_runner_adv(func: callable, backend: ConfigBackend, entrypoint=DEFAULT_ENTRYPOINT):
    """
    The non-decorator equivalent to @eunomia_adv(...)
    - This function is the core of eunomia, calling the relevant plugins, creating
      the merged config and finally calling your entry.
    """
    raise NotImplementedError


# ========================================================================= #
# Single Config Loading - No Wrapping                                       #
# ========================================================================= #


def eunomia_load(config=DEFAULT_CONFIG, entrypoint=DEFAULT_ENTRYPOINT):
    return eunomia_load_adv(
        backend=_eunomia_get_backend(config),
        entrypoint=entrypoint
    )


def eunomia_load_adv(backend: ConfigBackend, entrypoint=DEFAULT_ENTRYPOINT):
    loader = ConfigLoader(backend)
    return loader.load_config(entrypoint)


# ========================================================================= #
# Util                                                                      #
# ========================================================================= #


def _eunomia_get_backend(config=DEFAULT_CONFIG):
    if isinstance(config, (str, pathlib.Path)):
        # we assume the config is a path to the root folder for a YAML backend
        if isinstance(config, pathlib.Path):
            config = config.absolute()
        return DiskConfigLoader(config_root=config)
    elif isinstance(config, dict):
        # we assume that config is a dictionary for a Dictionary backend.
        # TODO: merge with Group OR add separate group backend
        return DictConfigLoader(data=config)
    else:
        raise TypeError(f'Unsupported config_root type: {config.__class__.__name__}')


# ========================================================================= #
# End                                                                       #
# ========================================================================= #




# if __name__ == '__main__':
#
#     root = Group()
#     root.add_option('default', {
#         '_defaults_': {
#             'group_a': 'conf_a1',
#             'group_b': 'conf_b2',
#         }
#     })
#
#     group_a = root.new_subgroup('group_a')
#     group_a.add_option('conf_a1', {'a_value': 1})
#     group_a.add_option('conf_a2', {'a_value': 2})
#
#     group_b = root.new_subgroup('group_b')
#     group_b.add_option('conf_b1', {'b_value': 1})
#     group_b.add_option('conf_b2', {'b_value': 2})
#
#     print(root.default._defaults_)
#
#
#     # root_group = dict(
#     #     default={
#     #         '_defaults_': {
#     #             'group_a': 'conf_a1',
#     #             'group_b': 'conf_b2',
#     #         }
#     #     },
#     #     group_a=dict(
#     #         conf_a1={
#     #             'a_value': 1
#     #         },
#     #         conf_a2={
#     #             'a_value': 2
#     #         },
#     #     ),
#     #     group_b=dict(
#     #         conf_b1={
#     #             'b_value': 1
#     #         },
#     #         conf_b2={
#     #             'b_value': 2
#     #         },
#     #     )
#     # )
#
#     # import yaml
#     # print(yaml.dump(eunomia(root, 'default')))
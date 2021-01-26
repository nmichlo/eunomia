"""
Eunomia config
- Simple hydra config like configuration using yaml 1.2
"""

__version__ = "0.0.1dev1"


# ========================================================================= #
# Export                                                                    #
# ========================================================================= #


from eunomia._config import DiskConfigLoader, MemConfigLoader


def eunomia(config_root='configs', config_name='default'):
    if isinstance(config_root, str):
        loader = DiskConfigLoader(config_root)
    elif isinstance(config_root, dict):
        loader = MemConfigLoader(config_root)
    else:
        raise TypeError(f'Unsupported config_root type: {config_root.__class__.__name__}')
    return loader.load_config(config_name)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

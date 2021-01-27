"""
Eunomia config
- Simple hydra config like configuration using yaml 1.2
"""

__version__ = "0.0.1dev1"


# ========================================================================= #
# Export                                                                    #
# ========================================================================= #


from eunomia._config import DiskConfigLoader, DictConfigLoader


def eunomia(config_root='configs', config_name='default'):
    if isinstance(config_root, str):
        loader = DiskConfigLoader(config_root)
    elif isinstance(config_root, dict):
        loader = DictConfigLoader(config_root)
    else:
        raise TypeError(f'Unsupported config_root type: {config_root.__class__.__name__}')
    return loader.load_config(config_name)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


class Group(object):

    def __init__(self):
        self._groups = {}
        self._confs = {}

    def new_subgroup(self, name) -> 'Group':
        assert name not in self._groups
        assert name not in self._confs
        self._groups[name] = Group()
        return self._groups[name]

    def add_conf(self, name, conf) -> 'Group':
        assert name not in self._groups
        assert name not in self._confs
        self._confs[name] = conf
        return self

    def get_subgroup(self, name):
        return self._groups[name]

    def get_conf(self, name):
        return self._confs[name]



if __name__ == '__main__':

    root = Group()
    root.add_conf('default', {
        '_defaults_': {
            'group_a': 'conf_a1',
            'group_b': 'conf_b2',
        }
    })

    group_a = root.new_subgroup('group_a')
    group_a.add_conf('conf_a1', {'a_value': 1})
    group_a.add_conf('conf_a2', {'a_value': 2})

    group_b = root.new_subgroup('group_b')
    group_b.add_conf('conf_b1', {'b_value': 1})
    group_b.add_conf('conf_b2', {'b_value': 2})


    # root_group = dict(
    #     default={
    #         '_defaults_': {
    #             'group_a': 'conf_a1',
    #             'group_b': 'conf_b2',
    #         }
    #     },
    #     group_a=dict(
    #         conf_a1={
    #             'a_value': 1
    #         },
    #         conf_a2={
    #             'a_value': 2
    #         },
    #     ),
    #     group_b=dict(
    #         conf_b1={
    #             'b_value': 1
    #         },
    #         conf_b2={
    #             'b_value': 2
    #         },
    #     )
    # )

    import yaml
    print(yaml.dump(eunomia(root, 'default')))
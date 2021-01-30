import ruamel.yaml as yaml
import sys
from eunomia._config_nodes import TupleNode, IgnoreNode, RefNode, EvalNode, InterpolateNode


# we need 3.6 or above for ordered dictionary support
assert sys.version_info[0] == 3 and sys.version_info[1] >= 6, 'Python 3.6 or above is required.'


# ========================================================================= #
# Yaml Loader                                                               #
# ========================================================================= #


class EunomiaSafeLoader(yaml.SafeLoader):

    def __init__(self, *args, always_interpolate_strings=True, **kwargs):
        super().__init__(*args, **kwargs)
        # custom config values
        self._always_interpolate_strings = always_interpolate_strings

    def construct_scalar(self, node):
        # we always want to interpolate strings!
        if self._always_interpolate_strings:
            if node.tag == u'tag:yaml.org,2002:str':
                assert isinstance(node.value, str), 'This should never happen!'
                return InterpolateNode(node.value)
        # otherwise construct like usual
        return super().construct_scalar(node)

    @classmethod
    def yaml_register_config_node(cls, class_):
        for tag in class_.TAGS:
            EunomiaSafeLoader.add_constructor(tag, class_.yaml_constructor)


EunomiaSafeLoader.yaml_register_config_node(TupleNode)
EunomiaSafeLoader.yaml_register_config_node(IgnoreNode)
EunomiaSafeLoader.yaml_register_config_node(RefNode)
EunomiaSafeLoader.yaml_register_config_node(EvalNode)
EunomiaSafeLoader.yaml_register_config_node(InterpolateNode)


# NOTE: unknown tags can be parsed
#       - https://github.com/kislyuk/yq/blob/2dd5cf39e18f2caf0c416e3da1c93a62bc801e0b/yq/loader.py#L57
# TODO: hydra adds the following implicit_resolvers & filters them
#       - float: https://github.com/omry/omegaconf/blob/ad593a527556583dfefa6d7dd34beec3f183a438/omegaconf/_utils.py#L106
#       - timestamp: https://github.com/omry/omegaconf/blob/ad593a527556583dfefa6d7dd34beec3f183a438/omegaconf/_utils.py#L120


# ========================================================================= #
# Yaml Util                                                                 #
# ========================================================================= #


def yaml_load(string):
    return yaml.load(string, EunomiaSafeLoader, version='1.2')


def yaml_load_file(path):
    with open(path, 'r') as f:
        return yaml_load(f.read())


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

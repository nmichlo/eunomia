import ruamel.yaml as yaml
import sys
from eunomia.values import IgnoreValue, RefValue, EvalValue, InterpolateValue


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
                return InterpolateValue(node.value)
        # otherwise construct like usual
        return super().construct_scalar(node)

    @classmethod
    def add_constructors(cls, tags: list, constructor):
        for tag in tags:
            cls.add_constructor(tag, constructor)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Custom Constructors                                                   #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def construct_custom_tuple(self, node: yaml.Node):
        if not isinstance(node, yaml.SequenceNode):
            raise yaml.YAMLError(f'tag {node.tag} for tuple(...) is not compatible with node: {node.__class__.__name__}. {repr(node.value)} must be a sequence/list')
        return tuple(self.construct_sequence(node))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Node Constructors                                                     #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def construct_node_ignore(self, node: yaml.Node):
        if not isinstance(node, yaml.ScalarNode):
            raise TypeError(f'tag {node.tag} for {IgnoreValue.__name__} is not compatible with node: {node.__class__.__name__} which is not a scalar.')
        return IgnoreValue(self.construct_scalar(node))

    def construct_node_ref(self, node: yaml.Node):
        return RefValue(self.construct_yaml_str(node))

    def construct_node_eval(self, node: yaml.Node):
        return EvalValue(self.construct_yaml_str(node))

    def construct_node_interpolate(self, node: yaml.Node):
        return InterpolateValue(self.construct_yaml_str(node))


EunomiaSafeLoader.add_constructors(['!tuple'], EunomiaSafeLoader.construct_custom_tuple)
EunomiaSafeLoader.add_constructors(['!str'], EunomiaSafeLoader.construct_node_ignore)
EunomiaSafeLoader.add_constructors(['!ref'], EunomiaSafeLoader.construct_node_ref)
EunomiaSafeLoader.add_constructors(['!eval'], EunomiaSafeLoader.construct_node_eval)
EunomiaSafeLoader.add_constructors(['!interp'], EunomiaSafeLoader.construct_node_interpolate)


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

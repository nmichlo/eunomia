import ruamel.yaml as yaml
import sys
from eunomia.nodes import TupleNode, IgnoreNode, RefNode, EvalNode, InterpolateNode


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
    def register_custom_constructor(cls, tags):
        def wrapper(constructor):
            for tag in tags:
                cls.add_constructor(tag, constructor)
            return None
        return wrapper

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Custom Constructors                                                   #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @register_custom_constructor(['!tuple'])
    def construct_custom_tuple(self, node: yaml.Node):
        if not isinstance(node, yaml.SequenceNode):
            raise yaml.YAMLError(f'tag {node.tag} for {TupleNode.__name__} is not compatible with node: {node.__class__.__name__}. {repr(node.value)} must be a sequence/list')
        return tuple(self.construct_sequence(node))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Node Constructors                                                     #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @register_custom_constructor(['!str'])
    def construct_node_ignore(self, node: yaml.Node):
        if not isinstance(node, yaml.ScalarNode):
            raise TypeError(f'tag {node.tag} for {IgnoreNode.__name__} is not compatible with node: {node.__class__.__name__}. {repr(node.value)} must be a scalar')
        return IgnoreNode(self.construct_scalar(node))

    @register_custom_constructor(['!ref'])
    def construct_node_ref(self, node: yaml.Node):
        return RefNode(self.construct_yaml_str(node))

    @register_custom_constructor(['!eval'])
    def construct_node_eval(self, node: yaml.Node):
        return EvalNode(self.construct_yaml_str(node))

    @register_custom_constructor(['!interp'])
    def construct_node_interpolate(self, node: yaml.Node):
        return InterpolateNode(self.construct_yaml_str(node))


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

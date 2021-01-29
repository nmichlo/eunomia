from eunomia._config_nodes import IgnoreNode, RefNode, EvalNode
import ruamel.yaml as yaml
import sys


# we need 3.6 or above for ordered dictionary support
assert sys.version_info[0] == 3 and sys.version_info[1] >= 6, 'Python 3.6 or above is required.'


# ========================================================================= #
# Yaml Loader                                                               #
# ========================================================================= #


class EunomiaSafeLoader(yaml.SafeLoader):

    def construct_tuple(self, node):
        if not isinstance(node, yaml.SequenceNode):
            raise yaml.YAMLError(f'{repr(node.tag)} {repr(node.value)} <<< must be a sequence/list')
        return tuple(self.construct_sequence(node))

    def construct_ref(self, node):
        return RefNode(self.construct_yaml_str(node))

    def construct_eval(self, node):
        return EvalNode(self.construct_yaml_str(node))

    def construct_raw(self, node):
        if isinstance(node, yaml.ScalarNode):
            value = self.construct_scalar(node)
        # elif isinstance(node, yaml.SequenceNode):
        #     value = self.construct_sequence(node)
        # elif isinstance(node, yaml.MappingNode):
        #     value = self.construct_mapping(node)
        else:
            raise TypeError(f'{IgnoreNode.TAG} is not compatible with node type: {node.__class__.__name__}')
        return str(value)

    def construct_scalar(self, node):
        if node.tag == u'tag:yaml.org,2002:str':
            assert isinstance(node.value, str), 'This should never happen!'
            if node.value[0:2] in ('f"', "f'") and node.value[1] == node.value[-1]:
                return EvalNode(node.value)
        return super().construct_scalar(node)


EunomiaSafeLoader.add_constructor('!tuple', EunomiaSafeLoader.construct_tuple)
EunomiaSafeLoader.add_constructor(RefNode.TAG, EunomiaSafeLoader.construct_ref)
EunomiaSafeLoader.add_constructor(EvalNode.TAG, EunomiaSafeLoader.construct_eval)
EunomiaSafeLoader.add_constructor(IgnoreNode.TAG, EunomiaSafeLoader.construct_raw)


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

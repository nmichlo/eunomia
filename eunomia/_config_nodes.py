from typing import Any, Union
import lark
from ruamel import yaml
from eunomia._interpreter import interpret_expr
from eunomia.grammar._lark import INTERPOLATE_PARSER, INTERPOLATE_RECONSTRUCTOR


# ========================================================================= #
# Base Loaders                                                              #
# ========================================================================= #


class Node(object):

    @property
    def TAGS(self) -> tuple[str]:
        raise NotImplementedError

    @property
    def INSTANCE_OF(self) -> Union[type, tuple[type, ...]]:
        raise NotImplementedError

    def __init__(self, value: str):
        assert isinstance(value, self.INSTANCE_OF), f'{value=} corresponding to {self.TAGS} must be instance of: {self.INSTANCE_OF}'
        self.raw_value = value

    def __repr__(self):
        return f'{self.__class__.__name__}(value={repr(self.raw_value)})'

    def __str__(self):
        return repr(self)

    def get_config_value(self, merged_config: dict, merged_defaults: dict):
        raise NotImplementedError

    @classmethod
    def yaml_constructor(cls, loader: yaml.SafeLoader, node: yaml.Node):
        raise NotImplementedError


# ========================================================================= #
# Basic Nodes                                                               #
# ========================================================================= #


class TupleNode(Node):

    TAGS = ('!tuple',)
    INSTANCE_OF = (list, tuple)

    def get_config_value(self, merged_config: dict, merged_defaults: dict):
        return tuple(self.raw_value)

    @classmethod
    def yaml_constructor(cls, loader: yaml.SafeLoader, node: yaml.Node):
        if not isinstance(node, yaml.SequenceNode):
            raise yaml.YAMLError(f'{repr(node.tag)} {repr(node.value)} <<< must be a sequence/list')
        return tuple(loader.construct_sequence(node))


class IgnoreNode(Node):

    TAGS = ('!str',)
    INSTANCE_OF = str

    def get_config_value(self, merged_config: dict, merged_defaults: dict):
        return self.raw_value

    @classmethod
    def yaml_constructor(cls, loader: yaml.SafeLoader, node: yaml.Node):
        if isinstance(node, yaml.ScalarNode):
            value = loader.construct_scalar(node)
        else:
            raise TypeError(f'{node.tag} for {IgnoreNode.__name__} is not compatible with node type: {node.__class__.__name__}')
        return str(value)


class RefNode(Node):

    TAGS = ('!ref',)
    INSTANCE_OF = str

    def get_config_value(self, merged_config: dict, merged_defaults: dict) -> Any:
        path, keys = self.raw_value, self.raw_value.split('.')
        # check that the keys are valid python identifiers
        if not keys:
            raise RuntimeError(f'Malformed {path=}, must contain at least one key.')
        for key in keys:
            if not str.isidentifier(key):
                raise RuntimeError(f'Malformed {key=} in {path=}, must be a valid identifier')
        # walk to get value
        value = merged_config
        for key in keys:
            value = value[key]
        return value

    @classmethod
    def yaml_constructor(cls, loader: yaml.SafeLoader, node: yaml.Node):
        return RefNode(loader.construct_yaml_str(node))


class EvalNode(Node):

    TAGS = ('!eval',)
    INSTANCE_OF = str

    def get_config_value(self, merged_config: dict, merged_defaults: dict):
        return interpret_expr(self.raw_value, usersyms={
            'C': merged_config,
            'D': merged_defaults,
            'CONFIG': merged_defaults,
            'DEFAULTS': merged_defaults,
        })

    @classmethod
    def yaml_constructor(cls, loader: yaml.SafeLoader, node: yaml.Node):
        return EvalNode(loader.construct_yaml_str(node))


# ========================================================================= #
# Interpolate Nodes                                                         #
# ========================================================================= #


class InterpolateNode(Node):

    TAGS = ('!interp',)
    INSTANCE_OF = (str, list)

    ALLOWED_SUB_NODES = (str, IgnoreNode, RefNode, EvalNode)

    def _check_subnodes(self, nodes: list):
        for subnode in nodes:
            if not isinstance(subnode, self.ALLOWED_SUB_NODES):
                raise TypeError(f'Malformed {InterpolateNode.__name__}, {subnode=} must be instance of: {self.ALLOWED_SUB_NODES}')

    def get_config_value(self, merged_config: dict, merged_defaults: dict) -> str:
        nodes = self.raw_value
        # convert string to nodes
        if isinstance(nodes, str):
            nodes = _string_to_interpolate_nodes(nodes)
        self._check_subnodes(nodes)
        # combine values together
        values = []
        for subnode in nodes:
            if not isinstance(subnode, str):
                subnode = subnode.get_config_value(merged_config, merged_defaults)
            values.append(subnode)
        # get final result
        if len(values) == 1:
            return values[0]
        return ''.join(str(v) for v in values)

    @classmethod
    def yaml_constructor(cls, loader: yaml.SafeLoader, node: yaml.Node):
        return InterpolateNode(loader.construct_yaml_str(node))


def _string_to_interpolate_nodes(string):
    nodes = INTERPOLATE_PARSER.parse(string)
    converted = InterpretLarkToConfNodesList().visit(nodes)
    return converted


class InterpretLarkToConfNodesList(lark.visitors.Interpreter):

    def interpolate(self, tree) -> list[Node]:
        if len(tree.children) != 1:
            raise RuntimeError('Malformed interpolate node. This should never happen!')
        return self.visit(tree.children[0])

    def interpolate_string(self, tree) -> list[Node]:
        return self.visit_children(tree)

    def interpret_fstring(self, tree) -> list[Node]:
        # TODO: having to wrap in a list here might be a grammar mistake
        return [
            EvalNode(INTERPOLATE_RECONSTRUCTOR.reconstruct(tree))
        ]

    def template_ref(self, tree): return RefNode(INTERPOLATE_RECONSTRUCTOR.reconstruct(tree))
    def template_exp(self, tree): return EvalNode(INTERPOLATE_RECONSTRUCTOR.reconstruct(tree))
    def str(self, node):          return IgnoreNode(INTERPOLATE_RECONSTRUCTOR.reconstruct(node))

    def __getattr__(self, item):
        raise RuntimeError(f'This should never happen! Unknown Interpolation Grammar Node Visited: {item}')


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

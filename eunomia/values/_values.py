from typing import Any, Union
import lark

from eunomia._util_traverse import PyTransformer
from eunomia.values._util_interpret import interpret_expr
from eunomia.values._util_lark import INTERPOLATE_RECONSTRUCTOR, INTERPOLATE_PARSER


# ========================================================================= #
# Base Loaders                                                              #
# ========================================================================= #


class BaseValue(object):

    @property
    def INSTANCE_OF(self) -> Union[type, tuple[type, ...]]:
        raise NotImplementedError

    def __init__(self, value: str):
        assert isinstance(value, self.INSTANCE_OF), f'{value=} corresponding to {self.__class__.__name__} must be instance of: {self.INSTANCE_OF}'
        self.raw_value = value

    def __repr__(self):
        return f'{self.__class__.__name__}(value={repr(self.raw_value)})'

    def __str__(self):
        return repr(self)

    def get_config_value(self, merged_config: dict, merged_options: dict, current_config: dict):
        raise NotImplementedError

    @classmethod
    def recursive_transform_config_value(cls, merged_config: dict, merged_options: dict, value):
        return RecursiveGetConfigValue(merged_config, merged_options).transform(value)

    def __eq__(self, other):
        if not isinstance(other, self.__class__): return False
        if not isinstance(self, other.__class__): return False
        return other.raw_value == self.raw_value

    def __hash__(self):
        return hash((self.__class__, self.raw_value))


class RecursiveGetConfigValue(PyTransformer):

    def __init__(self, merged_config: dict, merged_options: dict, current_config: dict):
        self._merged_config = merged_config
        self._merged_options = merged_options
        self._current_config = current_config

    def __transform_default__(self, value):
        if isinstance(value, BaseValue):
            return value.get_config_value(self._merged_config, self._merged_options, self._current_config)
        return value


def recursive_get_config_value_alt(merged_config: dict, merged_options: dict, current_config: dict, value: Any):
    return RecursiveGetConfigValue(merged_config, merged_options, current_config).transform(value)


# TODO: how much faster is this than the above?
def recursive_get_config_value(merged_config: dict, merged_options: dict, current_config: dict, value: Any):
    if isinstance(value, BaseValue):
        return value.get_config_value(merged_config, merged_options, current_config)
    elif isinstance(value, list):
        return list(recursive_get_config_value(merged_config, merged_options, current_config, v) for v in value)
    elif isinstance(value, tuple):
        return tuple(recursive_get_config_value(merged_config, merged_options, current_config, v) for v in value)
    elif isinstance(value, set):
        return set(recursive_get_config_value(merged_config, merged_options, current_config, v) for v in value)
    elif isinstance(value, dict):
        return {
            recursive_get_config_value(merged_config, merged_options, current_config, k):
                recursive_get_config_value(merged_config, merged_options, current_config, v)
            for k, v in value.items()
        }
    else:
        return value


# ========================================================================= #
# Basic Nodes                                                               #
# ========================================================================= #


class IgnoreValue(BaseValue):

    INSTANCE_OF = str

    def get_config_value(self, merged_config: dict, merged_options: dict, current_config: dict):
        return self.raw_value


class RefValue(BaseValue):

    INSTANCE_OF = str

    def get_config_value(self, merged_config: dict, merged_options: dict, current_config: dict) -> Any:
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


class EvalValue(BaseValue):

    INSTANCE_OF = str

    def get_config_value(self, merged_config: dict, merged_options: dict, current_config: dict):
        return interpret_expr(self.raw_value, usersyms={
            'this': current_config,
            'conf': merged_config,
            'opts': merged_options,
        })


# ========================================================================= #
# Interpolate Nodes                                                         #
# ========================================================================= #


class InterpolateValue(BaseValue):

    INSTANCE_OF = (str, list)
    ALLOWED_SUB_NODES = (str, IgnoreValue, RefValue, EvalValue)

    def _check_subnodes(self, nodes: list):
        for subnode in nodes:
            if not isinstance(subnode, self.ALLOWED_SUB_NODES):
                raise TypeError(f'Malformed {InterpolateValue.__name__}, {subnode=} must be instance of: {self.ALLOWED_SUB_NODES}')

    def get_config_value(self, merged_config: dict, merged_options: dict, current_config: dict) -> str:
        nodes = self.raw_value

        # convert string to nodes if necessary using lark
        # detects f-strings f"..." or f'...' and strings
        # with placeholders ${...} and ${=...} defined in
        # the lark grammar
        if isinstance(nodes, str):
            nodes = _string_to_interpolate_nodes(nodes)
        self._check_subnodes(nodes)

        # concatenate strings and interpolated values
        # obtained from calling this same function on
        # nodes and child nodes
        values = []
        for subnode in nodes:
            if not isinstance(subnode, str):
                subnode = recursive_get_config_value(merged_config, merged_options, current_config, subnode)
            values.append(subnode)

        # get final result -- return that actual value if its the
        # only value in the list, instead of merging to a string
        if len(values) == 1:
            return values[0]
        return ''.join(str(v) for v in values)


def _string_to_interpolate_nodes(string):
    nodes = INTERPOLATE_PARSER.parse(string)
    converted = _InterpretLarkToConfNodesList().visit(nodes)
    return converted


class _InterpretLarkToConfNodesList(lark.visitors.Interpreter):
    """
    This class walks a lark.Tree and converts the lark nodes as
    necessary to action nodes.
    - RefNode
    - EvalNode
    - IgnoreNode

    The lark nodes are defined in the interpolation grammar file.
    grammar_interpolate.lark
    """

    def interpolate(self, tree) -> list[BaseValue]:
        if len(tree.children) != 1:
            raise RuntimeError('Malformed interpolate node. This should never happen!')
        return self.visit(tree.children[0])

    def interpolate_string(self, tree) -> list[BaseValue]:
        return self.visit_children(tree)

    def interpret_fstring(self, tree) -> list[BaseValue]:
        # TODO: having to wrap in a list here might be a grammar mistake
        return [
            EvalValue(INTERPOLATE_RECONSTRUCTOR.reconstruct(tree))
        ]

    def template_ref(self, tree): return RefValue(INTERPOLATE_RECONSTRUCTOR.reconstruct(tree))
    def template_exp(self, tree): return EvalValue(INTERPOLATE_RECONSTRUCTOR.reconstruct(tree))
    def str(self, node):          return IgnoreValue(INTERPOLATE_RECONSTRUCTOR.reconstruct(node))

    def __getattr__(self, item):
        raise RuntimeError(f'This should never happen! Unknown Interpolation Grammar Node Visited: {item}')


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

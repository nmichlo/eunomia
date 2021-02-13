from typing import Any, Union, List, Tuple
import lark
from eunomia.config.nodes._util_interpret import interpret_expr
from eunomia.config.nodes._util_lark import SUB_RECONSTRUCTOR, SUB_PARSER
from eunomia.config import scheme as s

# ========================================================================= #
# Base Loaders                                                              #
# ========================================================================= #


class ConfigNode(object):

    @property
    def INSTANCE_OF(self) -> Union[type, Tuple[type, ...]]:
        raise NotImplementedError

    def __init__(self, value: str):
        assert isinstance(value, self.INSTANCE_OF), f'value={repr(value)} corresponding to {self.__class__.__name__} must be instance of: {self.INSTANCE_OF}'
        self.raw_value = value

    def __repr__(self):
        return f'{self.__class__.__name__}(value={repr(self.raw_value)})'

    def __str__(self):
        return repr(self)

    def get_config_value(self, merged_config: dict, merged_options: dict, current_config: dict):
        raise NotImplementedError

    def __eq__(self, other):
        if not isinstance(other, self.__class__): return False
        if not isinstance(self, other.__class__): return False
        return other.raw_value == self.raw_value

    def __hash__(self):
        return hash((self.__class__, self.raw_value))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Recursive Resolve                                                     #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    @staticmethod
    def recursive_get_config_value(merged_config: dict, merged_options: dict, current_config: dict, value: Any):
        if isinstance(value, ConfigNode):
            return value.get_config_value(merged_config, merged_options, current_config)
        elif isinstance(value, list):
            return list(ConfigNode.recursive_get_config_value(merged_config, merged_options, current_config, v) for v in value)
        elif isinstance(value, tuple):
            return tuple(ConfigNode.recursive_get_config_value(merged_config, merged_options, current_config, v) for v in value)
        elif isinstance(value, set):
            return set(ConfigNode.recursive_get_config_value(merged_config, merged_options, current_config, v) for v in value)
        elif isinstance(value, dict):
            return {
                ConfigNode.recursive_get_config_value(merged_config, merged_options, current_config, k):
                    ConfigNode.recursive_get_config_value(merged_config, merged_options, current_config, v)
                for k, v in value.items()
            }
        else:
            return value


# ========================================================================= #
# Basic Nodes                                                               #
# ========================================================================= #


class IgnoreNode(ConfigNode):

    INSTANCE_OF = str

    def get_config_value(self, merged_config: dict, merged_options: dict, current_config: dict):
        return self.raw_value


class RefNode(ConfigNode):

    INSTANCE_OF = str

    def get_config_value(self, merged_config: dict, merged_options: dict, current_config: dict) -> Any:
        # TODO: add support for groups in the merged_options, prefix with /
        keys, is_relative = s.split_pkg_path(self.raw_value)
        if is_relative:
            raise ValueError(f'reference cannot be a relative path, must be from root: {self.raw_value}')
        # walk to get value
        value = merged_config
        for key in keys:
            value = value[key]
            # resolve
            if isinstance(value, ConfigNode):
                value = value.get_config_value(merged_config, merged_options, current_config)
        return value


class EvalNode(ConfigNode):

    INSTANCE_OF = str

    def get_config_value(self, merged_config: dict, merged_options: dict, current_config: dict):
        return interpret_expr(
            self.raw_value,
            usersyms={
                'this': current_config,
                'conf': merged_config,
                'incl': merged_options,
            },
            NON_STANDARD_PYTHON=True  # try getitem on AttributeError
        )


# ========================================================================= #
# Substitute Nodes                                                          #
# ========================================================================= #


class SubNode(ConfigNode):

    INSTANCE_OF = (str, list)
    ALLOWED_SUB_NODES = (str, IgnoreNode, RefNode, EvalNode)

    def _check_subnodes(self, nodes: list):
        for subnode in nodes:
            if not isinstance(subnode, self.ALLOWED_SUB_NODES):
                raise TypeError(f'Malformed {SubNode.__name__}, subnode={repr(subnode)} must be instance of: {self.ALLOWED_SUB_NODES}')

    def get_config_value(self, merged_config: dict, merged_options: dict, current_config: dict) -> str:
        nodes = self.raw_value

        # 1. convert string to nodes if necessary using lark
        # detects f-strings f"..." or f'...' and strings
        # with placeholders ${...} and ${=...} defined in
        # the lark grammar
        if isinstance(nodes, str):
            nodes = _string_to_sub_nodes(nodes)
        self._check_subnodes(nodes)

        # 2. concatenate strings and substituted values
        # obtained from calling this same function on
        # nodes and child nodes
        values = []
        for subnode in nodes:
            if not isinstance(subnode, str):
                subnode = ConfigNode.recursive_get_config_value(merged_config, merged_options, current_config, subnode)
            values.append(subnode)

        # 3. get final result -- return that actual value if its the
        # only value in the list, instead of merging to a string
        if len(values) == 1:
            return values[0]
        return ''.join(str(v) for v in values)


def _string_to_sub_nodes(string):
    nodes = SUB_PARSER.parse(string)
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
    grammar_substitute.lark
    """

    def substitute(self, tree) -> List[ConfigNode]:
        if len(tree.children) != 1:
            raise RuntimeError('Malformed substitute node. This should never happen!')
        return self.visit(tree.children[0])

    def substitute_string(self, tree) -> List[ConfigNode]:
        return self.visit_children(tree)

    def interpret_fstring(self, tree) -> List[ConfigNode]:
        # TODO: having to wrap in a list here might be a grammar mistake
        return [
            EvalNode(SUB_RECONSTRUCTOR.reconstruct(tree))
        ]

    def template_ref(self, tree): return RefNode(SUB_RECONSTRUCTOR.reconstruct(tree))
    def template_exp(self, tree): return EvalNode(SUB_RECONSTRUCTOR.reconstruct(tree))

    # we no longer handle this due to the grammar change for CHAR and WSSTR
    # def str(self, node):        return IgnoreNode(SUB_RECONSTRUCTOR.reconstruct(node))

    def __getattr__(self, item):
        raise RuntimeError(f'This should never happen! Unknown Interpolation Grammar Node Visited: {item}')


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

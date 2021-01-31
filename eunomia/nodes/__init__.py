"""
Config nodes are used to represent actions that should be
performed during the merging of the config itself.
"""

from ._config_nodes import Node
from ._config_nodes import IgnoreNode, RefNode, EvalNode, InterpolateNode

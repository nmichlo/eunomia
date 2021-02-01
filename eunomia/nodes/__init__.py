"""
Config nodes are used to represent actions that should be
performed during the merging of the config itself.
"""

from ._action_nodes import ActionNode
from ._action_nodes import IgnoreNode, RefNode, EvalNode, InterpolateNode

"""
Config nodes are used to represent actions that should be
performed during the merging of the config itself.
"""

from ._lazy_nodes import LazyValueNode
from ._lazy_nodes import IgnoreNode, RefNode, EvalNode, InterpolateNode

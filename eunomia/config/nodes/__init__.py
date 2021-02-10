"""
Config nodes are used to represent actions that should be
performed during the merging of the config itself.
"""

from ._nodes import ConfigNode
from ._nodes import IgnoreNode, RefNode, EvalNode, SubNode

"""
Config nodes are used to represent actions that should be
performed during the merging of the config itself.
"""

from ._values import BaseValue
from ._values import IgnoreValue, RefValue, EvalValue, InterpolateValue

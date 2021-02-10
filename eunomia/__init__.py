"""
Eunomia config
- Simple hydra config like configuration using yaml 1.2
"""


# ========================================================================= #
# Check                                                                     #
# ========================================================================= #


from sys import version_info as _V
# we need 3.6 or above for ordered dictionary support
assert _V[0] == 3 and _V[1] >= 6, 'Python 3.6 or above is required for ordered dictionary support.'


# ========================================================================= #
# Export Core                                                               #
# ========================================================================= #


# eunomia decorator
from ._core import eunomia, eunomia_adv
# eunomia runner
from ._core import eunomia_runner, eunomia_runner_adv
# eunomia simple loader - skips plugins and runners
from ._core import eunomia_load, eunomia_load_adv


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

"""
Eunomia config
- Simple hydra config like configuration using yaml 1.2
"""


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

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
from eunomia.core import eunomia
# eunomia runner
from eunomia.core import eunomia_runner
# eunomia simple loader - skips plugins and runners
from eunomia.core import eunomia_load


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

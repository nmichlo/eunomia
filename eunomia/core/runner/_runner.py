import warnings
from typing import List

from eunomia.backend import Backend, ValidConfigTypes
from eunomia.core.sweep import _yield_list_sweep, _num_list_sweep_iterations


# ========================================================================= #
# Base Runner                                                               #
# ========================================================================= #


class BaseRunner(object):

    WARN_SWEEPS = 128

    def __init__(self, no_output=True):
        self._no_output = no_output

    def run(self, func: callable, config: ValidConfigTypes, entrypoint: str, overrides: List[str], backend: Backend):
        # avoid circular import
        from eunomia import eunomia_load

        # get default values
        if overrides is None:
            overrides = []

        # check number of sweeps to be performed
        num_sweeps = _num_list_sweep_iterations(overrides)
        if num_sweeps > self.WARN_SWEEPS:
            warnings.warn(f'number of sweeps seems high: {num_sweeps}')

        # iterate over all sweeps
        for i, (new_overrides, changed) in enumerate(_yield_list_sweep(overrides)):
            merged_config = eunomia_load(config, entrypoint, new_overrides, backend)
            self._run(i+1, num_sweeps, func, merged_config, changed)

    def _run(self, i, num_sweeps, func, merged_config, changed):
        raise NotImplementedError


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

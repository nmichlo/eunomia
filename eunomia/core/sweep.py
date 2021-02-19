import os as _os
from typing import Iterable as _Iterable, Dict as _Dict


# ========================================================================= #
# Config Loader                                                             #
# ========================================================================= #


class _SweepList(object):
    def __iter__(self):
        raise NotImplementedError
    def __str__(self):
        return f"<{str(list(self))[1:-1]}>"


class _Choices(_SweepList):
    def __init__(self, choices: _Iterable):
        assert isinstance(choices, _Iterable)
        self._iterable = choices
    def __iter__(self):
        yield from self._iterable


class _Reverse(_Choices):
    def __iter__(self):
        yield from reversed(self._iterable)


class _Sort(_Choices):
    def __init__(self, choices: _Iterable, reverse=False):
        super().__init__(choices)
        self._reverse = reverse
    def __iter__(self):
        items = sorted(self._iterable)
        yield from reversed(items) if self._reverse else items

# used internally
class _Single(_SweepList):
    def __init__(self, value):
        self._value = value
    def __iter__(self):
        yield self._value

class _Options(_SweepList):
    def __init__(self, group: str, options: list):
        self._group = group
        self._options = options
    def __iter__(self):
        from eunomia.config import Group
        # handle group
        options = self._options
        if isinstance(options, Group):
            options = options.options.values()
        # return values
        for option in self._options:
            yield {self._group: option}

# rename
sort = _Sort
reverse = _Reverse
choices = _Choices
options = _Options


# ========================================================================= #
# Iterate                                                                   #
# ========================================================================= #


def _get_flat_sweepable(dct: _Dict[str, object]):
    return {k: v for k, v in dct.items() if isinstance(v, _SweepList)}


def _pretty_flat_sweepable(dct: _Dict[str, object]) -> str:
    return f"[{', '.join(f'{k}={v}' for k, v in dct.items())}]"


def _num_flat_sweep_iterations(dct: _Dict[str, object]):
    count = 1
    for v in _get_flat_sweepable(dct).values():
        count *= len(list(v))
    return count


def _yield_flat_dct_sweep(dct: _Dict[str, object], return_sweep=True):
    """
    dct must be a flat dictionary with values that should
    be product-iterated in instances of SweepList.

    Note that if not SweepList values are found, only one item is returned.
    """
    permutable = _get_flat_sweepable(dct)
    import itertools
    for values in itertools.product(*permutable.values()):
        sweep = dict(zip(permutable.keys(), values))
        merged = {**dct, **sweep}
        yield (merged, sweep) if return_sweep else merged


def _num_list_sweep_iterations(values: list):
    count = 1
    for v in (v for v in values if isinstance(v, _SweepList)):
        count *= len(list(v))
    return count


def _yield_list_sweep(values: list, return_sweep=True):
    permutable = [v for i, v in enumerate(values) if isinstance(v, _SweepList)]
    indices    = [i for i, v in enumerate(values) if isinstance(v, _SweepList)]
    # permutable = [v if isinstance(v, _SweepList) else _Single(v) for v in values]
    import itertools
    for sweep in itertools.product(*permutable):
        merged = list(values)
        for i, v in zip(indices, sweep):
            merged[i] = v
        yield (merged, sweep) if return_sweep else merged

# ========================================================================= #
# End                                                                       #
# ========================================================================= #

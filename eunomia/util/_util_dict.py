from numbers import Number
from typing import Iterable, List, Tuple, Type


# ========================================================================= #
# Recursive Dictionary Helper                                               #
# ========================================================================= #


def recursive_getitem(dct, keys: Iterable[str], make_missing=False):
    if not keys:
        return dct
    (key, *keys) = keys
    if make_missing:
        if key not in dct:
            dct[key] = {}
    return recursive_getitem(dct[key], keys, make_missing=make_missing)


def recursive_setitem(dct, keys: Iterable[str], value, make_missing=False):
    if not keys:
        raise KeyError(f'{recursive_setitem.__name__} requires as least one key: {keys}')
    (*keys, key) = keys
    insert_at = recursive_getitem(dct, keys, make_missing=make_missing)
    insert_at[key] = value


def dict_recursive_update(left, right, allow_overwrite=True, safe_merge=True, allow_update_types: List[Tuple[Type, ...]] = None):
    # check type groups
    if allow_update_types is None:
        allow_update_types = []
    # allow floats and integers to mix by default
    allow_update_types = [(Number,)] + allow_update_types
    # check user groups
    assert all(isinstance(group, tuple) for group in allow_update_types)
    # begin merge!
    _dict_recursive_update(left, right, [], allow_overwrite=allow_overwrite, safe_merge=safe_merge, type_merge_groups=allow_update_types)


def _dict_recursive_update(left, right, stack, allow_overwrite, safe_merge, type_merge_groups):
    # right overwrites left
    for k, rv in right.items():
        if k not in left:
            left[k] = rv
        else:
            # get values
            lv = left[k]
            # handle cases
            # -- l and r are dictionaries
            if isinstance(lv, dict) and isinstance(rv, dict):
                _dict_recursive_update(left[k], rv, stack=stack + [k], allow_overwrite=allow_overwrite, safe_merge=safe_merge, type_merge_groups=type_merge_groups)
                continue
            if not allow_overwrite:
                raise KeyError('cannot overwrite existing key!')
            # -- l and r have different types
            if type(lv) is not type(rv):
                if not any(isinstance(lv, group) and isinstance(rv, group) for group in type_merge_groups):
                    if safe_merge:
                        raise TypeError(f'with safe_merge=True, {dict_recursive_update.__name__} cannot update keys with different types l={type(lv).__name__} r={type(rv).__name__}.\nError occurred at key: {stack + [k]}')
            left[k] = rv

# ========================================================================= #
# End                                                                       #
# ========================================================================= #

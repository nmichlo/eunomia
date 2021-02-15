from typing import Iterable


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
    (key, *keys) = keys
    insert_at = recursive_getitem(dct, keys, make_missing=make_missing)
    insert_at[key] = value


def dict_recursive_update(left, right):
    _dict_recursive_update(left, right, [])


def _dict_recursive_update(left, right, stack):
    # right overwrites left
    for k, v in right.items():
        if k in left:
            if isinstance(left[k], dict) or isinstance(v, dict):
                new_stack = stack + [k]
                if not (isinstance(left[k], dict) and isinstance(v, dict)):
                    raise TypeError(f'Recursive update cannot merge keys with a different type if one is a dictionary. {".".join(new_stack)}')
                else:
                    _dict_recursive_update(left[k], v, stack=new_stack)
                    continue
        left[k] = v


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

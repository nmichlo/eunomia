from copy import deepcopy
from numbers import Number

import pytest
from eunomia import _util_dict as u

def test_dict_util():
    _left = dict(a=1, b=dict(a=10, b=20))

    left = deepcopy(_left)
    assert u.recursive_getitem(left, ['a']) == 1
    assert u.recursive_getitem(left, ['b', 'a']) == 10
    assert u.recursive_getitem(left, []) is left
    assert u.recursive_getitem(left, ['b']) is left['b']

    # set values
    left = deepcopy(_left)
    u.recursive_setitem(left, ['a'], 10)
    assert left['a'] == 10
    u.recursive_setitem(left, ['b', 'a'], 22)
    assert left['b']['a'] == 22

    # missing keys
    left = deepcopy(_left)
    u.recursive_setitem(left, ['c'], 42)  # alright because its the last one
    u.recursive_setitem(left, ['b', 'c'], 42)  # alright because its the last one
    with pytest.raises(KeyError, match='d'):
        u.recursive_setitem(left, ['d', 'a'], 42)
    u.recursive_setitem(left, ['d', 'a'], 42, make_missing=True)
    assert left == dict(a=1, b=dict(a=10, b=20, c=42), c=42, d=dict(a=42))
    with pytest.raises(KeyError, match='requires as least one key'):
        u.recursive_setitem(left, [], 42)

    # overwrite
    left = deepcopy(_left)
    u.recursive_setitem(left, ['b'], 42)
    assert left == dict(a=1, b=42)

    # update
    left = deepcopy(_left)
    u.dict_recursive_update(left, right=dict(c=42))
    assert left == dict(a=1, b=dict(a=10, b=20), c=42)

    # update -- both dictionaries
    left = deepcopy(_left)
    u.dict_recursive_update(left, right=dict(b=dict(a=42)))
    assert left == dict(a=1, b=dict(a=42, b=20))

    # update -- different types
    left = deepcopy(_left)
    with pytest.raises(TypeError, match='cannot update keys with different types'):
        u.dict_recursive_update(left, right=dict(b=42))

    left = deepcopy(_left)
    with pytest.raises(TypeError, match='cannot update keys with different types'):
        u.dict_recursive_update(left, right=dict(b=42), safe_merge=True)

    left = deepcopy(_left)
    u.dict_recursive_update(left, right=dict(b=42), safe_merge=False)
    assert left == dict(a=1, b=42)

    left = deepcopy(_left)
    u.dict_recursive_update(left, right=dict(b=42), safe_merge=True, allow_update_types=[(dict, int)])
    assert left == dict(a=1, b=42)

    # floats and integers should be allowed together, this is a special case

    _left = dict(a=1, b=7.7, c=(1,2,3))

    left = deepcopy(_left)
    with pytest.raises(TypeError, match='cannot update keys with different types'):
        u.dict_recursive_update(left, right=dict(c=42))
    left = deepcopy(_left)
    u.dict_recursive_update(left, right=dict(b=42))

    # MAYBE?
    # lists and tuples should be allowed together, this is a special case
    # lists replace lists
    # left = deepcopy(_left)
    # u.dict_recursive_update(left, right=dict(c=[2,3,4]))

import pytest

from eunomia.backend import BackendDict
from eunomia.config import Group, Option


# ========================================================================= #
# Test Eunomia                                                              #
# ========================================================================= #


def test_config_objects():

    bk = BackendDict()

    left = Group(dict(
        suboption1=Option(dict(foo=1)),
        subgroup1=Group(dict(
            suboption1=Option(dict(foo=1)),
        )),
    ))

    right = Group(dict(
        suboption2=Option(dict(foo=2)),
        subgroup1=Group(dict(
            suboption2=Option(dict(foo=2)),
        )),
        subgroup2=Group(dict(
            suboption1=Option(dict(foo=1)),
            suboption2=Option(dict(foo=2)),
        )),
    ))

    # absorb
    left.absorb_children(right)
    with pytest.raises(TypeError, match='group can only absorb other groups'):
        left.absorb_children(Option())
    with pytest.raises(AssertionError, match='tried to absorb group from the same tree'):
        left.absorb_children(left.get_subgroup('subgroup1'))

    target = Group(dict(
        suboption1=Option(dict(foo=1)),
        suboption2=Option(dict(foo=2)),
        subgroup1=Group(dict(
            suboption1=Option(dict(foo=1)),
            suboption2=Option(dict(foo=2)),
        )),
        subgroup2=Group(dict(
            suboption1=Option(dict(foo=1)),
            suboption2=Option(dict(foo=2)),
        )),
    ))

    # checks
    assert bk.dump(left) == bk.dump(target)
    assert bk.dump(right) == bk.dump(Group())

    right2 = Group(dict(
        subgroup1=Group(dict(
            suboption1=Option(dict(foo=1)),
        )),
    ))

    target2 = Group(dict(
        suboption1=Option(dict(foo=1)),
        suboption2=Option(dict(foo=2)),
        subgroup1=Group(dict(
            suboption1=Option(dict(foo=1)),
            suboption2=Option(dict(foo=2)),
        )),
        subgroup2=Group(dict(
            suboption1=Option(dict(foo=1)),
            suboption2=Option(dict(foo=2)),
            subgroup1=Group(dict(
                suboption1=Option(dict(foo=1)),
            )),
        )),
    ))

    left.get_subgroup('subgroup2').absorb_children(right2)

    assert bk.dump(left) == bk.dump(target2)
    assert bk.dump(right) == bk.dump(Group())

    right3 = Group(dict(
        subgroup2=Group(dict(
            suboption1=Option(dict(foo=111)),
            subgroup1=Group(dict(
                suboption1=Option(dict(foo=111)),
            )),
        )),
    ))

    target3 = Group(dict(
        suboption1=Option(dict(foo=1)),
        suboption2=Option(dict(foo=2)),
        subgroup1=Group(dict(
            suboption1=Option(dict(foo=1)),
            suboption2=Option(dict(foo=2)),
        )),
        subgroup2=Group(dict(
            suboption1=Option(dict(foo=111)),
            suboption2=Option(dict(foo=2)),
            subgroup1=Group(dict(
                suboption1=Option(dict(foo=111)),
            )),
        )),
    ))

    # check conflict, both roots
    with pytest.raises(KeyError, match="left group '/' cannot absorb right group '/' because conflicting left option was found"):
        left.absorb_children(right3)
    # check conflict, right is child
    _right3_root = Group(dict(parentgroup=right3))
    with pytest.raises(KeyError, match="left group '/' cannot absorb right group '/parentgroup' because conflicting left option was found"):
        left.absorb_children(right3)
    assert bk.dump(left) == bk.dump(target2)
    # check conflict, left is child and right is child
    _left_root = Group(dict(parentgroup=left))
    with pytest.raises(KeyError, match="left group '/parentgroup' cannot absorb right group '/parentgroup' because conflicting left option was found"):
        left.absorb_children(right3)
    assert bk.dump(left) == bk.dump(target2)
    # check conflict, left is child
    _right3_root.del_subgroup('parentgroup')
    with pytest.raises(KeyError, match="left group '/parentgroup' cannot absorb right group '/' because conflicting left option was found"):
        left.absorb_children(right3)
    assert bk.dump(left) == bk.dump(target2)
    # check conflict, both roots, AGAIN
    _left_root.del_subgroup('parentgroup')
    with pytest.raises(KeyError, match="left group '/' cannot absorb right group '/' because conflicting left option was found"):
        left.absorb_children(right3)
    assert bk.dump(left) == bk.dump(target2)

    # merge with overwrite enabled
    left.absorb_children(right3, allow_replace_options=True)
    assert bk.dump(left) == bk.dump(target3)

from pprint import pprint

import pytest
from eunomia import eunomia_load
from eunomia.config import Group, Option
from eunomia.values import InterpolateValue, EvalValue
from eunomia.config import scheme as s


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def test_simple_config():
    g = Group({
        'subgroup': Group({
            'suboption2': Option({'bar': 2}),
            'suboption1': Option({'bar': 1}),
        }),
        'subgroup2': Group({
            'sub2option1': Option({'baz': 1}),
            'sub2option2': Option({'baz': 2}),
        }),
        'default': Option({
            'foo': 1
        }),
    })

    # forward and backwards conversion!
    d1 = g.to_dict()
    g1 = Group.from_dict(d1)
    assert repr(g1) == repr(g)

    # forward and backwards conversion!
    d2 = g.to_compact_dict()
    g2 = Group.from_compact_dict(d2)
    assert repr(g2) == repr(g)


def _make_config_group(suboption='suboption1', suboption2=None, package1='<group>', package2='<group>') -> Group:
    g = Group({
        'subgroup': Group({
            'suboption1': Option({'bar': 1}, pkg=package1),
            'suboption2': Option({'bar': 2}, pkg=package1),
        }),
        'subgroup2': Group({
            'sub2option1': Option({'baz': 1}, pkg=package2),
            'sub2option2': Option({'baz': 2}, pkg=package2),
        }),
        'default': Option(
            data={'foo': 1},
            opts={
                **({'subgroup': suboption} if suboption else {}),
                **({'subgroup2': suboption2} if suboption2 else {}),
            }
        ),
    })

    # # forward and backwards conversion!
    # d1 = g.to_dict()
    # g1 = Group.from_dict(d1)
    # assert repr(g1) == repr(g)
    #
    # # forward and backwards conversion!
    # d2 = g.to_compact_dict()
    # g2 = Group.from_compact_dict(d2)
    # assert repr(g2) == repr(g)
    #
    # print(g)
    # print(g1)
    # print(g2)


def test_config_objects():
    _make_config_group(suboption='suboption1')
    _make_config_group(suboption='suboption2')
    _make_config_group(suboption='invalid___')  # invalid but not an error


# ========================================================================= #
# Test Eunomia                                                              #
# ========================================================================= #


# def test_eunomia_loader():
#     # check no subgroups
#     assert eunomia_load(_make_config_group(suboption=None)) == {'foo': 1}
#
#     # test subgroup
#     assert eunomia_load(_make_config_group(suboption='suboption1')) == {'subgroup': {'bar': 1}, 'foo': 1}
#     assert eunomia_load(_make_config_group(suboption='suboption2')) == {'subgroup': {'bar': 2}, 'foo': 1}
#     with pytest.raises(Exception):
#         eunomia_load(_make_config_group(suboption='invalid___'))
#
#     # test second subgroup
#     assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='sub2option1')) == {'subgroup': {'bar': 2}, 'subgroup2': {'baz': 1}, 'foo': 1}
#     assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='sub2option2')) == {'subgroup': {'bar': 2}, 'subgroup2': {'baz': 2}, 'foo': 1}
#
#     # test root package
#     assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='_root_')) == {'bar': 1, 'subgroup2': {'baz': 2}, 'foo': 1}
#     assert eunomia_load(_make_config_group(suboption2='sub2option2', package2='_root_')) == {'subgroup': {'bar': 1}, 'baz': 2, 'foo': 1}
#     assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='_root_', package2='_root_')) == {'bar': 1, 'baz': 2, 'foo': 1}
#
#     # test custom package
#     assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='asdf', package2='fdsa.asdf')) == {'asdf': {'bar': 1}, 'fdsa': {'asdf': {'baz': 2}}, 'foo': 1}
#     assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='asdf', package2='asdf.fdsa')) == {'asdf': {'bar': 1, 'fdsa': {'baz': 2}}, 'foo': 1}
#     assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='asdf', package2=InterpolateValue('${="asdf"}.fdsa'))) == {'asdf': {'bar': 1, 'fdsa': {'baz': 2}}, 'foo': 1}
#
#     # test interpolation values
#     assert eunomia_load(_make_config_group(suboption=InterpolateValue('suboption${=1}'))) == {'subgroup': {'bar': 1}, 'foo': 1}
#     assert eunomia_load(_make_config_group(suboption=InterpolateValue('f"suboption{1}"'))) == {'subgroup': {'bar': 1}, 'foo': 1}
#     assert eunomia_load(_make_config_group(suboption=EvalValue('f"suboption{2}"'))) == {'subgroup': {'bar': 2}, 'foo': 1}
#     assert eunomia_load(_make_config_group(suboption=InterpolateValue('suboption${foo}'))) == {'subgroup': {'bar': 1}, 'foo': 1}
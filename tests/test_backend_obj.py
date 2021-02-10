import pytest
from schema import SchemaError

from eunomia.config import Group, Option
from eunomia.config import scheme as s


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def test_simple_option():
    Option(data={'foo': 'bar'}).to_dict()
    Option(data={'foo': 'bar'}, pkg=s.PKG_ROOT).to_dict()
    Option(data={'foo': 'bar'}, pkg=s.PKG_GROUP).to_dict()

    Option(data={'foo': 'bar'}, opts={}).to_dict()

    # test relative path
    Option(data={'foo': 'bar'}, opts={'group1': 'option1'}).to_dict()
    Option(data={'foo': 'bar'}, opts={'group1/group2': 'option2'}).to_dict()
    # test absolute path
    Option(data={'foo': 'bar'}, opts={'/group1/group2': 'option2'}).to_dict()

    with pytest.raises(SchemaError, match='is_identifier'):
        Option(data={'foo': 'bar'}, opts={'group1': '1invalid'}).to_dict()
    with pytest.raises(SchemaError, match='Wrong key'):
        Option(data={'foo': 'bar'}, opts={'1invalid': 'option2'}).to_dict()
    with pytest.raises(SchemaError, match='Wrong key'):
        Option(data={'foo': 'bar'}, opts={'group1/2invalid': 'option2'}).to_dict()

    Option(data={'foo': 'bar'}, pkg='key1').to_dict()
    Option(data={'foo': 'bar'}, pkg='key1.key2').to_dict()


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


def _make_config_group(suboption='suboption1', suboption2=None, package1='<group>', package2='<group>', check_cycle=False) -> Group:
    g = Group({
        'subgroup': Group({
            'suboption1': Option({'bar': 1}, pkg=package1),
            'suboption2': Option({'bar': 2}, pkg=package1),
        }),
        'subgroup2': Group({
            'subgroup3': Group({
                'sub2option1': Option({'baz': 1}, pkg=package2),
                'sub2option2': Option({'baz': 2}, pkg=package2),
            }),
        }),
        'default': Option(
            data={'foo': 1},
            opts={
                **({'subgroup': suboption} if suboption else {}),  # relative
                **({'/subgroup2/subgroup3': suboption2} if suboption2 else {}),  # absolute
            }
        ),
    })

    if check_cycle:
        # forward and backwards conversion!
        d1 = g.to_dict()
        g1 = Group.from_dict(d1)
        assert repr(g1) == repr(g)
        # forward and backwards conversion!
        d2 = g.to_compact_dict()
        g2 = Group.from_compact_dict(d2)
        assert repr(g2) == repr(g)

    return g


def test_config_objects():
    _make_config_group(suboption='suboption1', check_cycle=True)
    _make_config_group(suboption='suboption2', check_cycle=True)
    _make_config_group(suboption='invalid___', check_cycle=True)  # invalid but not an error


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

import pytest

from eunomia.backend import BackendDict
from eunomia.config import Group, Option
from eunomia.config import keys as K


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def test_simple_option():
    bk = BackendDict()

    bk.dump_option(Option(data={'foo': 'bar'}))
    bk.dump_option(Option(data={'foo': 'bar'}, pkg=K.PKG_ROOT))
    bk.dump_option(Option(data={'foo': 'bar'}, pkg=K.PKG_GROUP))

    bk.dump_option(Option(data={'foo': 'bar'}, defaults=[]))

    # test relative path
    bk.dump_option(Option(data={'foo': 'bar'}, defaults=['group1/option1']))
    bk.dump_option(Option(data={'foo': 'bar'}, defaults=['group1/group2/option2']))
    # test absolute path
    bk.dump_option(Option(data={'foo': 'bar'}, defaults=['/group1/group2/option2']))

    with pytest.raises(ValueError):  # TODO: fix error messages, match='is_identifier'):
        bk.dump_option(Option(data={'foo': 'bar'}, defaults=[{'group1': '1invalid'}]))
    with pytest.raises(ValueError):  # TODO: fix error messages, match='Wrong key'):
        bk.dump_option(Option(data={'foo': 'bar'}, defaults=[{'1invalid': 'option2'}]))
    with pytest.raises(ValueError):  # TODO: fix error messages, match='Wrong key'):
        bk.dump_option(Option(data={'foo': 'bar'}, defaults=[{'group1/2invalid': 'option2'}]))

    bk.dump_option(Option(data={'foo': 'bar'}, pkg='key1'))
    bk.dump_option(Option(data={'foo': 'bar'}, pkg='key1.key2'))


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

    bck = BackendDict()

    # forward and backwards conversion!
    d1 = BackendDict().dump(g)
    g1 = BackendDict().load_group(d1)
    assert repr(g1) == repr(g)


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
            defaults=[
                *([{'subgroup': suboption}] if suboption else []),  # relative
                *([{'/subgroup2/subgroup3': suboption2}] if suboption2 else []),  # absolute
            ],
        ),
    })

    if check_cycle:
        # forward and backwards conversion!
        d1 = BackendDict().dump(g)
        g1 = BackendDict().load_group(d1)
        assert repr(g1) == repr(g)

    return g


def test_config_objects():
    _make_config_group(suboption='suboption1', check_cycle=True)
    _make_config_group(suboption='suboption2', check_cycle=True)
    _make_config_group(suboption='invalid___', check_cycle=True)  # invalid but not an error


def test_option_init():
    # raw data in option
    data = {'foo': 'bar'}
    defaults = ['/group1/group2/option2']
    pkg = K.PKG_ROOT
    # make equivalent options
    option = Option(data=data, defaults=defaults, pkg=pkg)
    # check circular conversion
    bk = BackendDict()
    assert bk.dump(option) == bk.dump(bk.load_option(bk.dump(option)))


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

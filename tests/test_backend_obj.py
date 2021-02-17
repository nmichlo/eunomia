import re

import pytest

from eunomia.backend import BackendDict
from eunomia.config.nodes import SubNode
from tests.util import temp_capture_stdout
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


def test_debug_groups():
    root = _make_config_group(suboption='suboption1')

    with temp_capture_stdout() as out:
        root.debug_tree_print()
    color_out = out.getvalue()
    assert color_out == ' \x1b[90m\x1b[0m\x1b[35m/\x1b[0m\n \x1b[90m├\x1b[93m╌\x1b[0m \x1b[90m/:\x1b[0m \x1b[33mdefault\x1b[0m\n \x1b[90m├\x1b[95m─\x1b[0m \x1b[90m\x1b[0m\x1b[35m/subgroup\x1b[0m\n \x1b[90m│\x1b[0m  \x1b[90m├\x1b[93m╌\x1b[0m \x1b[90m/subgroup:\x1b[0m \x1b[33msuboption1\x1b[0m\n \x1b[90m│\x1b[0m  \x1b[90m╰\x1b[93m╌\x1b[0m \x1b[90m/subgroup:\x1b[0m \x1b[33msuboption2\x1b[0m\n \x1b[90m╰\x1b[95m─\x1b[0m \x1b[90m\x1b[0m\x1b[35m/subgroup2\x1b[0m\n    \x1b[90m╰\x1b[95m─\x1b[0m \x1b[90m/subgroup2\x1b[0m\x1b[35m/subgroup3\x1b[0m\n       \x1b[90m├\x1b[93m╌\x1b[0m \x1b[90m/subgroup2/subgroup3:\x1b[0m \x1b[33msub2option1\x1b[0m\n       \x1b[90m╰\x1b[93m╌\x1b[0m \x1b[90m/subgroup2/subgroup3:\x1b[0m \x1b[33msub2option2\x1b[0m\n'

    with temp_capture_stdout() as out:
        root.debug_tree_print(colors=False)
    normal_out = out.getvalue()
    assert normal_out == ' /\n ├╌ /: default\n ├─ /subgroup\n │  ├╌ /subgroup: suboption1\n │  ╰╌ /subgroup: suboption2\n ╰─ /subgroup2\n    ╰─ /subgroup2/subgroup3\n       ├╌ /subgroup2/subgroup3: sub2option1\n       ╰╌ /subgroup2/subgroup3: sub2option2\n'
    # https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
    assert normal_out == re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', color_out)

    with temp_capture_stdout() as out:
        root.debug_tree_print(colors=False, show_defaults=True)
    normal_out_defaults = out.getvalue()
    assert normal_out_defaults == ' /\n ├╌ /: default [subgroup: suboption1]\n ├─ /subgroup\n │  ├╌ /subgroup: suboption1\n │  ╰╌ /subgroup: suboption2\n ╰─ /subgroup2\n    ╰─ /subgroup2/subgroup3\n       ├╌ /subgroup2/subgroup3: sub2option1\n       ╰╌ /subgroup2/subgroup3: sub2option2\n'

    root = _make_config_group(suboption=SubNode('suboption${=1}'))
    with temp_capture_stdout() as out:
        root.debug_tree_print(colors=False, show_defaults=True)
    normal_out_defaults_special = out.getvalue()
    assert normal_out_defaults_special == ' /\n ├╌ /: default [subgroup: suboption${=1}]\n ├─ /subgroup\n │  ├╌ /subgroup: suboption1\n │  ╰╌ /subgroup: suboption2\n ╰─ /subgroup2\n    ╰─ /subgroup2/subgroup3\n       ├╌ /subgroup2/subgroup3: sub2option1\n       ╰╌ /subgroup2/subgroup3: sub2option2\n'


    # TODO: test other flags

# ========================================================================= #
# END                                                                       #
# ========================================================================= #

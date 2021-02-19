from eunomia import eunomia_runner
from eunomia.config import Group, Option
from eunomia.core.sweep import options, sort, choices, reverse


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def test_local_sweep():

    config = Group({
        'default': Option(defaults=[{'/foo': 'foo1'}, {'/bar': '*'}]),
        'foo': Group({
            'foo1': Option(data=dict(foo1=1), pkg='<root>'),
            'foo2': Option(data=dict(foo2=2), pkg='<root>'),
            'foo3': Option(data=dict(foo3=3), pkg='<root>'),
            'foo4': Option(data=dict(foo4=4), pkg='<root>'),
            'foo5': Option(data=dict(foo5=5), pkg='<root>'),
        }),
        'bar': Group({
            'bar1': Option(data=dict(bar1=1), pkg='<root>'),
            'bar2': Option(data=dict(bar2=2), pkg='<root>'),
            'bar3': Option(data=dict(bar3=3), pkg='<root>'),
            'bar4': Option(data=dict(bar4=4), pkg='<root>'),
            'bar5': Option(data=dict(bar5=5), pkg='<root>'),
        })
    })

    def run(overrides=None):
        configs = []
        def test(config):
            configs.append(config)
        eunomia_runner(test, config=config, overrides=overrides)
        return configs

    assert run(overrides=None) == [
        {'bar1': 1, 'bar2': 2, 'bar3': 3, 'bar4': 4, 'bar5': 5, 'foo1': 1}
    ]

    assert run(overrides=[options('foo', [[], '*'])]) == [
        {'bar1': 1, 'bar2': 2, 'bar3': 3, 'bar4': 4, 'bar5': 5},
        {'bar1': 1, 'bar2': 2, 'bar3': 3, 'bar4': 4, 'bar5': 5, 'foo1': 1, 'foo2': 2, 'foo3': 3, 'foo4': 4, 'foo5': 5}
    ]

    assert run(overrides=[options('bar', ['bar1', 'bar2', []])]) == [
        {'bar1': 1, 'foo1': 1},
        {'bar2': 2, 'foo1': 1},
        {'foo1': 1}
    ]

    assert run(overrides=[options('bar', sort(['bar3', 'bar1']))]) == [
        {'bar1': 1, 'foo1': 1},
        {'bar3': 3, 'foo1': 1},
    ]

    assert run(overrides=[options('bar', sort(['bar1', 'bar3']))]) == [
        {'bar1': 1, 'foo1': 1},
        {'bar3': 3, 'foo1': 1},
    ]

    assert run(overrides=[options('bar', sort(['bar1', 'bar3'], reverse=True))]) == [
        {'bar3': 3, 'foo1': 1},
        {'bar1': 1, 'foo1': 1},
    ]

    assert run(overrides=[choices([{'bar': 'bar1'}, {'foo': 'foo2'}])]) == [
        {'bar1': 1, 'foo1': 1},
        {'bar1': 1, 'bar2': 2, 'bar3': 3, 'bar4': 4, 'bar5': 5, 'foo2': 2}
    ]

    assert run(overrides=[reverse(choices([{'bar': 'bar1'}, {'foo': 'foo2'}]))]) == [
        {'bar1': 1, 'bar2': 2, 'bar3': 3, 'bar4': 4, 'bar5': 5, 'foo2': 2},
        {'bar1': 1, 'foo1': 1},
    ]

    assert run(overrides=[options('foo', ['foo3', ['foo1', 'foo4']]), options('bar', ['bar1', 'bar2', []])]) == [
        {'bar1': 1, 'foo3': 3},
        {'bar2': 2, 'foo3': 3},
        {'foo3': 3},
        {'bar1': 1, 'foo1': 1, 'foo4': 4},
        {'bar2': 2, 'foo1': 1, 'foo4': 4},
        {'foo1': 1, 'foo4': 4}
    ]


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

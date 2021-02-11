from eunomia.config import Group, Option
from eunomia.registry import RegistryGroup


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def foo(bar, baz=1):
    return bar, baz


def test_simple_option():
    root = RegistryGroup()

    _foo = foo
    _foo = root.register()(_foo)
    _foo = root.register(option_name='foo_alt')(_foo)
    _foo = root.register(option_name='foo_alt2', group_path='/group/subgroup')(_foo)
    _foo = root.register(option_name='foo_alt3', group_path='/group/subgroup', override_defaults=dict(baz=2))(_foo)
    assert _foo is foo

    target = Group({
        'tests': Group({
            'test_registry': Group({
                'foo': Option({'_target_': 'tests.test_registry.foo', 'baz': 1}),
                'foo_alt': Option({'_target_': 'tests.test_registry.foo', 'baz': 1}),
            })
        }),
        'group': Group({
            'subgroup': Group({
                'foo_alt2': Option({'_target_': 'tests.test_registry.foo', 'baz': 1}),
                'foo_alt3': Option({'_target_': 'tests.test_registry.foo', 'baz': 2}),
            })
        })
    })

    # NOTE: the working directory must not be /eunomia/tests, it must be /eunomia
    assert root.to_dict() == target.to_dict()

# ========================================================================= #
# END                                                                       #
# ========================================================================= #

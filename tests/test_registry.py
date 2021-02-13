import pytest

from eunomia import eunomia_load
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

    # test defaults
    # - if is_default is not specified, then the default can be overwritten
    #   otherwise it cannot be

    assert root.get_registered_defaults() == {'tests/test_registry': 'foo'}
    assert root.get_registered_defaults(explicit_only=True) == {}

    _foo = root.register(option_name='foo_alt4', group_path='/group/subgroup', override_defaults=dict(baz=3), is_default=True)(_foo)

    assert root.get_registered_defaults() == {'group/subgroup': 'foo_alt4'}
    assert root.get_registered_defaults(explicit_only=True) == {'group/subgroup': 'foo_alt4'}

    # test that the registrable group is the root.
    g = Group({'temp': root})
    with pytest.raises(AssertionError, match='Can only register on the root node.'): root.register()(_foo)
    with pytest.raises(AssertionError, match='Can only register on the root node.'): root.get_registered_defaults()

    # reset
    root._parent = None
    root._key = None

    # try again
    # TODO: maybe update to better error message
    with pytest.raises(KeyError, match='parent already has child with key: foo'): root.register()(_foo)
    assert root.get_registered_defaults() == {'group/subgroup': 'foo_alt4'}

    # try include group
    root.add_option('default', Option(include=root.get_registered_defaults()))
    assert eunomia_load(root) == {'group': {'subgroup': {'_target_': 'tests.test_registry.foo', 'baz': 3}}}


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

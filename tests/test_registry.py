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
    assert RegistryGroup().register(foo) is foo    # @register
    assert RegistryGroup().register()(foo) is foo  # @register()

    root = RegistryGroup()

    _foo = foo
    _foo = root.register()(_foo)
    _foo = root.register(option_name='foo_alt')(_foo)
    _foo = root.register(option_name='foo_alt2', group_path='/group/subgroup')(_foo)
    _foo = root.register(option_name='foo_alt3', group_path='/group/subgroup', override_params=dict(baz=2))(_foo)
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

    _foo = root.register(option_name='foo_alt4', group_path='/group/subgroup', override_params=dict(baz=3), is_default=True)(_foo)
    # this should fail because it was also marked as the default
    with pytest.raises(AssertionError, match='registered callable .* for option: .* was previously explicitly registered as a default.'):
        root.register(option_name='foo_alt4_CHECK', group_path='/group/subgroup', override_params=dict(baz=3), is_default=True)(_foo)
    # this should not fail as the above failed
    root.register(option_name='foo_alt4_CHECK', group_path='/group/subgroup', override_params=dict(baz=3), is_default=False)(_foo)

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

    # try merge group
    root.add_option('default', Option(defaults=root.get_registered_defaults()))
    assert eunomia_load(root) == {'group': {'subgroup': {'_target_': 'tests.test_registry.foo', 'baz': 3}}}


def fizz(foo, bar, buzz=1, baz=1):
    return foo, bar, buzz, baz


def test_override_modes():
    def _register(**kwargs):
        root = RegistryGroup().register_fn(fizz, **kwargs)
        root.add_option('default', Option(defaults=root.get_registered_defaults()))
        return eunomia_load(root)

    with pytest.raises(KeyError, match='Invalid override mode: \'INVALID\''):
        _register(override_mode='INVALID')

    # should be any
    assert _register()                     == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}
    assert _register(include_kwargs=True)  == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}
    assert _register(include_kwargs=False) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz'}}}
    assert _register(include_kwargs=True, override_params=dict(baz=2)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 2}}}
    assert _register(include_kwargs=False, override_params=dict(baz=2)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'baz': 2}}}

    # mode: any
    assert _register(include_kwargs=True, override_mode='any')  == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}
    assert _register(include_kwargs=False, override_mode='any') == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz'}}}
    assert _register(include_kwargs=True, override_mode='any', override_params=dict(buzz=5))  == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 5, 'baz': 1}}}
    assert _register(include_kwargs=False, override_mode='any', override_params=dict(buzz=5)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 5}}}
    assert _register(include_kwargs=False, override_mode='any', override_params=dict(foo=7)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'foo': 7}}}
    assert _register(include_kwargs=True, override_mode='any', override_params=dict(foo=7, bar=7)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'foo': 7, 'bar': 7, 'baz': 1, 'buzz': 1}}}
    assert _register(include_kwargs=True, override_mode='any', override_params=dict(foo=7, bar=7, buzz=5)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'foo': 7, 'bar': 7, 'baz': 1, 'buzz': 5}}}
    with pytest.raises(AssertionError, match="cannot override params: \\['bazz']"):
        _register(include_kwargs=True, override_mode='any', override_params=dict(foo=7, bar=7, buzz=5, bazz=-1))

    # mode: kwargs
    assert _register(include_kwargs=True, override_mode='kwargs')  == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}
    assert _register(include_kwargs=False, override_mode='kwargs') == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz'}}}
    assert _register(include_kwargs=True, override_mode='kwargs', override_params=dict(buzz=5))  == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 5, 'baz': 1}}}
    assert _register(include_kwargs=False, override_mode='kwargs', override_params=dict(buzz=5)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 5}}}
    with pytest.raises(AssertionError, match="cannot override params: \\['foo']"):
        _register(include_kwargs=False, override_mode='kwargs', override_params=dict(foo=7))
    with pytest.raises(AssertionError, match="cannot override params: \\['foo', 'bar']"):
        _register(include_kwargs=True, override_mode='kwargs', override_params=dict(foo=7, bar=7))
    with pytest.raises(AssertionError, match="cannot override params: \\['foo', 'bar']"):
        _register(include_kwargs=True, override_mode='kwargs', override_params=dict(foo=7, bar=7, buzz=5))

    # made: all
    with pytest.raises(AssertionError, match="all non-default parameters require an override: \\['foo', 'bar']"):
        _register(include_kwargs=True, override_mode='all')
    with pytest.raises(AssertionError, match="all non-default parameters require an override: \\['foo', 'bar']"):
        _register(include_kwargs=False, override_mode='all')
    with pytest.raises(AssertionError, match="all non-default parameters require an override: \\['foo']"):
        _register(include_kwargs=True, override_mode='all', override_params=dict(bar=7))
    with pytest.raises(AssertionError, match="all non-default parameters require an override: \\['bar']"):
        _register(include_kwargs=False, override_mode='all', override_params=dict(foo=7))
    assert _register(include_kwargs=False, override_mode='all', override_params=dict(foo=7, bar=7)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'bar': 7, 'foo': 7}}}
    assert _register(include_kwargs=True, override_mode='all', override_params=dict(foo=7, bar=7)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'bar': 7, 'foo': 7, 'buzz': 1, 'baz': 1}}}


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

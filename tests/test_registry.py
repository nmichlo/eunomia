import pytest

from eunomia import eunomia_load
from eunomia.config import Group, Option
from eunomia.registry import RegistryGroup


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def foo(bar, baz=1):  # pragma: no cover
    return bar, baz


def test_simple_option():
    assert RegistryGroup().register_target(foo) is foo    # @register
    assert RegistryGroup().register_target()(foo) is foo  # @register()

    root = RegistryGroup()

    _foo = foo
    _foo = root.register_target()(_foo)
    _foo = root.register_target(name='foo_alt')(_foo)
    _foo = root.register_target(name='foo_alt2', path='/group/subgroup')(_foo)
    _foo = root.register_target(name='foo_alt3', path='/group/subgroup', params=dict(baz=2))(_foo)
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

    assert root.get_registered_defaults() == [{'tests/test_registry': 'foo'}]
    assert root.get_registered_defaults(explicit_only=True) == []

    _foo = root.register_target(name='foo_alt4', path='/group/subgroup', params=dict(baz=3), is_default=True)(_foo)
    # this should fail because it was also marked as the default
    with pytest.raises(AssertionError, match='registered callable .* for option: .* was previously explicitly registered as a default.'):
        root.register_target(name='foo_alt4_CHECK', path='/group/subgroup', params=dict(baz=3), is_default=True)(_foo)
    # this should not fail as the above failed
    root.register_target(name='foo_alt4_CHECK', path='/group/subgroup', params=dict(baz=3), is_default=False)(_foo)

    assert root.get_registered_defaults() == [{'group/subgroup': 'foo_alt4'}]
    assert root.get_registered_defaults(explicit_only=True) == [{'group/subgroup': 'foo_alt4'}]

    # test that the registrable group is the root.
    g = Group({'temp': root})
    with pytest.raises(AssertionError, match='Can only register on the root node.'): root.register_target()(_foo)
    with pytest.raises(AssertionError, match='Can only register on the root node.'): root.get_registered_defaults()

    # reset
    root._parent = None
    root._key = None

    # try again
    # TODO: maybe update to better error message
    with pytest.raises(KeyError, match='parent already has child with key: foo'): root.register_target()(_foo)
    assert root.get_registered_defaults() == [{'group/subgroup': 'foo_alt4'}]

    # try merge group
    root.add_option('default', Option(defaults=root.get_registered_defaults()))
    assert eunomia_load(root) == {'group': {'subgroup': {'_target_': 'tests.test_registry.foo', 'baz': 3}}}


def fizz(foo, bar, buzz=1, baz=1):  # pragma: no cover
    return foo, bar, buzz, baz


def test_override_modes():
    def _register(**kwargs):
        root = RegistryGroup()
        root.register_target_fn(fizz, **kwargs)
        root.add_option('default', Option(defaults=root.get_registered_defaults()))
        return eunomia_load(root)

    with pytest.raises(KeyError, match='Invalid override mode: \'INVALID\''):
        _register(mode='INVALID')

    # should be any
    assert _register() == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}
    assert _register(keep_defaults=True)  == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}
    assert _register(keep_defaults=False) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz'}}}
    assert _register(keep_defaults=True, params=dict(baz=2)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 2}}}
    assert _register(keep_defaults=False, params=dict(baz=2)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'baz': 2}}}

    # mode: any
    assert _register(keep_defaults=True, mode='any')  == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}
    assert _register(keep_defaults=False, mode='any') == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz'}}}
    assert _register(keep_defaults=True, mode='any', params=dict(buzz=5))  == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 5, 'baz': 1}}}
    assert _register(keep_defaults=False, mode='any', params=dict(buzz=5)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 5}}}
    assert _register(keep_defaults=False, mode='any', params=dict(foo=7)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'foo': 7}}}
    assert _register(keep_defaults=True, mode='any', params=dict(foo=7, bar=7)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'foo': 7, 'bar': 7, 'baz': 1, 'buzz': 1}}}
    assert _register(keep_defaults=True, mode='any', params=dict(foo=7, bar=7, buzz=5)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'foo': 7, 'bar': 7, 'baz': 1, 'buzz': 5}}}
    with pytest.raises(AssertionError, match="cannot override params: \\['bazz']"):
        _register(keep_defaults=True, mode='any', params=dict(foo=7, bar=7, buzz=5, bazz=-1))

    # mode: kwargs
    assert _register(keep_defaults=True, mode='kwargs')  == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}
    assert _register(keep_defaults=False, mode='kwargs') == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz'}}}
    assert _register(keep_defaults=True, mode='kwargs', params=dict(buzz=5))  == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 5, 'baz': 1}}}
    assert _register(keep_defaults=False, mode='kwargs', params=dict(buzz=5)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 5}}}
    with pytest.raises(AssertionError, match="cannot override params: \\['foo']"):
        _register(keep_defaults=False, mode='kwargs', params=dict(foo=7))
    with pytest.raises(AssertionError, match="cannot override params: \\['foo', 'bar']"):
        _register(keep_defaults=True, mode='kwargs', params=dict(foo=7, bar=7))
    with pytest.raises(AssertionError, match="cannot override params: \\['foo', 'bar']"):
        _register(keep_defaults=True, mode='kwargs', params=dict(foo=7, bar=7, buzz=5))

    # made: all
    with pytest.raises(AssertionError, match="all non-default parameters require an override: \\['foo', 'bar']"):
        _register(keep_defaults=True, mode='all')
    with pytest.raises(AssertionError, match="all non-default parameters require an override: \\['foo', 'bar']"):
        _register(keep_defaults=False, mode='all')
    with pytest.raises(AssertionError, match="all non-default parameters require an override: \\['foo']"):
        _register(keep_defaults=True, mode='all', params=dict(bar=7))
    with pytest.raises(AssertionError, match="all non-default parameters require an override: \\['bar']"):
        _register(keep_defaults=False, mode='all', params=dict(foo=7))
    assert _register(keep_defaults=False, mode='all', params=dict(foo=7, bar=7)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'bar': 7, 'foo': 7}}}
    assert _register(keep_defaults=True, mode='all', params=dict(foo=7, bar=7)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'bar': 7, 'foo': 7, 'buzz': 1, 'baz': 1}}}

    # made: unchecked
    assert _register(keep_defaults=True, mode='unchecked') == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'baz': 1, 'buzz': 1}}}
    assert _register(keep_defaults=False, mode='unchecked') == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz'}}}
    assert _register(keep_defaults=True, mode='unchecked', params=dict(INVALID=1)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'baz': 1, 'buzz': 1, 'INVALID': 1}}}
    assert _register(keep_defaults=False, mode='unchecked', params=dict(INVALID=1)) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'INVALID': 1}}}

    # test nesting inside option and extra data
    assert _register() == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}
    assert _register(nest_path='targ1') == {'tests': {'test_registry': {'targ1': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}}
    assert _register(nest_path='targ1.targ2') == {'tests': {'test_registry': {'targ1': {'targ2': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}}}
    assert _register(nest_path='targ1', data={'asdf': 1}) == {'tests': {'test_registry': {'asdf': 1, 'targ1': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}}
    assert _register(nest_path='targ1', data={'targ1': {}}) == {'tests': {'test_registry': {'targ1': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}}}
    with pytest.raises(ValueError, match='nested object in data must be empty, otherwise target conflicts can occur'):
        _register(nest_path='targ1', data={'targ1': {'foo': 1}})
    with pytest.raises(ValueError, match='nested object in data must be a dictionary that the target can be merged into'):
        _register(nest_path='targ1', data={'targ1': []})
    assert _register(nest_path='targ1', pkg='<root>') == {'targ1': {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}}
    assert _register(pkg='<root>') == {'_target_': 'tests.test_registry.fizz', 'buzz': 1, 'baz': 1}


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

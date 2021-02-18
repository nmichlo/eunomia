import pytest

from eunomia import eunomia_load
from eunomia.backend import BackendDict
from eunomia.config import Group, Option
from eunomia.config.nodes import SubNode
from eunomia.registry import RegistryGroup
from eunomia.util._util_dict import recursive_setitem


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
    assert BackendDict().dump(root) == BackendDict().dump(target)

    # test defaults
    # - if is_default is not specified, then the default can be overwritten
    #   otherwise it cannot be

    assert root.get_registered_defaults() == [{'/tests/test_registry': 'foo'}]
    assert root.get_registered_defaults(explicit_only=True) == []

    _foo = root.register_target(name='foo_alt4', path='/group/subgroup', params=dict(baz=3), is_default=True)(_foo)
    # this should fail because it was also marked as the default
    with pytest.raises(AssertionError, match='registered callable .* for option: .* was previously explicitly registered as a default.'):
        root.register_target(name='foo_alt4_CHECK', path='/group/subgroup', params=dict(baz=3), is_default=True)(_foo)
    # this should not fail as the above failed
    root.register_target(name='foo_alt4_CHECK', path='/group/subgroup', params=dict(baz=3), is_default=False)(_foo)

    assert root.get_registered_defaults() == [{'/group/subgroup': 'foo_alt4'}]
    assert root.get_registered_defaults(explicit_only=True) == [{'/group/subgroup': 'foo_alt4'}]

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
    assert root.get_registered_defaults() == [{'/group/subgroup': 'foo_alt4'}]

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



def test_registry_with_options_as_defaults():

    registry = RegistryGroup()
    option_foo = registry.register_target_fn(foo, params=dict(bar=20))
    option_fizz = registry.register_target_fn(fizz, params=dict(foo=10, bar=20))

    registry.add_option('default', Option(defaults=[option_foo]))
    assert eunomia_load(registry) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.foo', 'bar': 20, 'baz': 1}}}

    with pytest.raises(KeyError, match='parent already has child with key'):
        registry.add_option('default', Option(defaults=[option_foo, option_fizz]))

    registry.del_option('default')
    registry.add_option('default', Option(defaults=[option_fizz]))
    assert eunomia_load(registry) == {'tests': {'test_registry': {'_target_': 'tests.test_registry.fizz', 'foo': 10, 'bar': 20, 'buzz': 1, 'baz': 1}}}


def fn(name='N/A'):
    return name


def test_registry_with_options_as_defaults_advanced():
    registry = RegistryGroup()

    # data type -- what kind of data is being used, this affects what type of data wrapper is needed for the framework
    data_type = registry.get_group_recursive('auto/data_type', make_missing=True)
    type_ground_truth = data_type.new_option('ground_truth', pkg='auto', data=dict(data_type='ground_truth'))
    type_episodes     = data_type.new_option('episodes',     pkg='auto', data=dict(data_type='episodes'))

    # data wrap mode -- how many inputs needs to be sampled to form a single observation from the dataset
    data_wrap_mode = registry.get_group_recursive('auto/data_wrap_mode', make_missing=True)
    wrap_triples = data_wrap_mode.new_option('triples', pkg='auto', data=dict(data_wrap_mode='triples'), defaults=[SubNode('/auto/data_wrapper/${auto.data_type}_${auto.data_wrap_mode}')])
    wrap_pairs   = data_wrap_mode.new_option('pairs',   pkg='auto', data=dict(data_wrap_mode='pairs'),   defaults=[SubNode('/auto/data_wrapper/${auto.data_type}_${auto.data_wrap_mode}')])
    wrap_single  = data_wrap_mode.new_option('single',  pkg='auto', data=dict(data_wrap_mode='single'),  defaults=[SubNode('/auto/data_wrapper/${auto.data_type}_${auto.data_wrap_mode}')])

    # dataset wrappers
    registry.register_target(fn, name='ground_truth_single',     params=dict(name='ground_truth_single'),     path='auto/data_wrapper')
    registry.register_target(fn, name='ground_truth_pairs',      params=dict(name='ground_truth_pairs'),      path='auto/data_wrapper')
    registry.register_target(fn, name='ground_truth_weak_pairs', params=dict(name='ground_truth_weak_pairs'), path='auto/data_wrapper')
    registry.register_target(fn, name='ground_truth_triples',    params=dict(name='ground_truth_triples'),    path='auto/data_wrapper')
    registry.register_target(fn, name='episodes_single',         params=dict(name='episodes_single'),         path='auto/data_wrapper')  # num_samples=1, sample_radius=32))
    registry.register_target(fn, name='episodes_pairs',          params=dict(name='episodes_pairs'),          path='auto/data_wrapper')  # num_samples=2, sample_radius=32))
    registry.register_target(fn, name='episodes_triples',        params=dict(name='episodes_triples'),        path='auto/data_wrapper')  # num_samples=3, sample_radius=32))

    # data
    registry.register_target(fn, name='dsprites',       params=dict(name='dsprites'),       path='disent/data', defaults=[type_ground_truth])
    registry.register_target(fn, name='monte_rollouts', params=dict(name='monte_rollouts'), path='disent/data', defaults=[type_episodes])

    # frameworks
    registry.register_target(fn, name='betavae', params=dict(name='betavae'), path='disent/framework', nest_path='cfg', defaults=[wrap_single])
    registry.register_target(fn, name='adavae',  params=dict(name='adavae'),  path='disent/framework', nest_path='cfg', defaults=[wrap_pairs])
    registry.register_target(fn, name='tvae',    params=dict(name='tvae'),    path='disent/framework', nest_path='cfg', defaults=[wrap_triples])

    def check(in_data, in_framework, out_data_type, out_data_wrap_mode):
        if registry.has_suboption('default'):
            registry.del_option('default')

        registry.new_option('default', defaults=[
            {'/disent/data': in_data},
            {'/disent/framework': in_framework},
        ])

        assert eunomia_load(registry) == {'disent': {'data': {'_target_': 'tests.test_registry.fn', 'name': in_data}, 'framework': {'cfg': {'_target_': 'tests.test_registry.fn', 'name': in_framework}}}, 'auto': {'data_type': out_data_type, 'data_wrap_mode': out_data_wrap_mode, 'data_wrapper': {'_target_': 'tests.test_registry.fn', 'name': f'{out_data_type}_{out_data_wrap_mode}'}}}

    check('dsprites', 'betavae', 'ground_truth', 'single')
    check('dsprites', 'adavae', 'ground_truth', 'pairs')
    check('dsprites', 'tvae', 'ground_truth', 'triples')

    check('monte_rollouts', 'betavae', 'episodes', 'single')
    check('monte_rollouts', 'adavae', 'episodes', 'pairs')
    check('monte_rollouts', 'tvae', 'episodes', 'triples')

    # CHECK MULTIPLE OPTIONS IN A SINGLE DEFAULT

    option_metric_dci = registry.register_target_fn(fn, name='metric_dci', params=dict(name='metric_dci'), pkg='<option>', path='disent/metrics')
    option_metric_mig = registry.register_target_fn(fn, name='metric_mig', params=dict(name='metric_mig'), pkg='<option>', path='disent/metrics')
    option_metric_fvs = registry.register_target_fn(fn, name='metric_fvs', params=dict(name='metric_fvs'), pkg='<option>', path='disent/metrics')

    def check(defaults, out_metrics, pkg_keys=None):
        if registry.has_suboption('default'):
            registry.del_option('default')

        registry.new_option('default', defaults=defaults)

        output = {}
        merged_metrics = {
            metric: {'_target_': 'tests.test_registry.fn', 'name': metric}
            for metric in out_metrics
        }
        recursive_setitem(output, ['disent', 'metrics'], merged_metrics, make_missing=True)

        assert eunomia_load(registry) == output

    # check that we can load all of them
    check(defaults=['/disent/metrics/metric_dci'], out_metrics=['metric_dci'])
    check(defaults=[option_metric_dci], out_metrics=['metric_dci'])

    check(defaults=[{'/disent/metrics': ['/disent/metrics/metric_dci', '/disent/metrics/metric_mig']}], out_metrics=['metric_dci', 'metric_mig'])
    check(defaults=[{'/disent/metrics': ['/disent/metrics/metric_dci', option_metric_mig]}], out_metrics=['metric_dci', 'metric_mig'])
    check(defaults=[{'/disent/metrics': '*'}], out_metrics=['metric_dci', 'metric_mig', 'metric_fvs'])

    check(defaults=[{'/disent/metrics': [option_metric_dci, option_metric_mig]}], out_metrics=['metric_dci', 'metric_mig'])
    check(defaults=[{'/disent/metrics': [option_metric_dci, option_metric_mig, option_metric_fvs]}], out_metrics=['metric_dci', 'metric_mig', 'metric_fvs'])

    # check that the group can be added itself
    check([registry.get_group_recursive('/disent/metrics')], ['metric_dci', 'metric_mig', 'metric_fvs'])



# ========================================================================= #
# END                                                                       #
# ========================================================================= #

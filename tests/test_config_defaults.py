import pytest

from eunomia.config._default import Default
from eunomia.config.nodes import ConfigNode
from tests.test_backend_obj import _make_config_group


# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def _resolver(string):
    if isinstance(string, ConfigNode):
        return string.get_config_value({}, {}, {})
    return string


def _resolve_default(group, default):
    # we are testing this! \/ \/ \/
    g, c, pkg, is_self = default.to_resolved_components(group, _resolver)
    # we are testing this! /\ /\ /\
    return g.abs_path, [c.abs_path for c in c], pkg


def test_defaults():

    root = _make_config_group(suboption=None, suboption2=None, package1='<option>', package2='asdf.fdsa')

    d = root.get_option_recursive('default')
    s1 = root.get_group_recursive('subgroup')
    s1o1 = root.get_option_recursive('subgroup/suboption1')
    s1o2 = root.get_option_recursive('subgroup/suboption2')
    s2 = root.get_group_recursive('subgroup2')
    s2s3 = root.get_group_recursive('subgroup2/subgroup3')
    s2s3o1 = root.get_option_recursive('subgroup2/subgroup3/suboption1')
    s2s3o2 = root.get_option_recursive('subgroup2/subgroup3/suboption2')

    # multiple different versions
    assert _resolve_default(root, Default(d))                   == ('/', ['/default'], ())
    assert _resolve_default(root, Default({root: d}))           == ('/', ['/default'], ())
    assert _resolve_default(root, Default({root: [d]}))         == ('/', ['/default'], ())
    assert _resolve_default(root, Default({'/': 'default'}))    == ('/', ['/default'], ())
    assert _resolve_default(root, Default({'/': '/default'}))   == ('/', ['/default'], ())
    assert _resolve_default(root, Default({'/': ['/default']})) == ('/', ['/default'], ())
    assert _resolve_default(root, Default({'/': ['default']}))  == ('/', ['/default'], ())

    # these should throw errors, option points to option
    with pytest.raises(KeyError, match='key .* is not a group'): _resolve_default(root, Default({'/default': ['default']}))
    with pytest.raises(KeyError, match='key .* is not a group'): _resolve_default(root, Default({d: d}))
    with pytest.raises(KeyError, match='key .* is not a group'): _resolve_default(root, Default({d: [d]}))

    # allow group to represent all suboptions
    assert _resolve_default(root, Default('')) == ('/', ['/default'], ())  # technically this is valid, its just confusing... should it be disabled?
    assert _resolve_default(root, Default('default')) == ('/', ['/default'], ())  # we want relative support in case we use group.absorb for example
    assert _resolve_default(root, Default('/')) == ('/', ['/default'], ())
    assert _resolve_default(root, Default('/default')) == ('/', ['/default'], ())
    assert _resolve_default(root, Default(root)) == ('/', ['/default'], ())
    assert _resolve_default(root, Default({'/': '/'})) == ('/', ['/default'], ())
    assert _resolve_default(root, Default({'/': '*'})) == ('/', ['/default'], ())
    assert _resolve_default(root, Default({root: '*'})) == ('/', ['/default'], ())
    assert _resolve_default(root, Default({root: root})) == ('/', ['/default'], ())
    assert _resolve_default(root, Default({'/': root})) == ('/', ['/default'], ())
    # these should throw errors, group points to group in list
    with pytest.raises(KeyError, match='value in list .* is not an option'): _resolve_default(root, Default({'/': ['subgroup']}))
    with pytest.raises(KeyError, match='value in list .* is not an option'): _resolve_default(root, Default({'/': ['default', 'subgroup']}))

    # check parents
    assert _resolve_default(root, Default(d)) == ('/', ['/default'], ())
    assert _resolve_default(s1, Default(d)) == ('/', ['/default'], ())
    assert _resolve_default(s2, Default(d)) == ('/', ['/default'], ())
    assert _resolve_default(s2s3, Default(d)) == ('/', ['/default'], ())

    # check others
    assert _resolve_default(root, Default(s1))        == ('/subgroup', ['/subgroup/suboption1', '/subgroup/suboption2'], ('subgroup',))
    assert _resolve_default(s1,   Default(s1))        == ('/subgroup', ['/subgroup/suboption1', '/subgroup/suboption2'], ('subgroup',))
    assert _resolve_default(s2,   Default(s1))        == ('/subgroup', ['/subgroup/suboption1', '/subgroup/suboption2'], ('subgroup',))
    assert _resolve_default(s2s3, Default(s1))        == ('/subgroup', ['/subgroup/suboption1', '/subgroup/suboption2'], ('subgroup',))
    assert _resolve_default(root, Default({s1: '*'})) == ('/subgroup', ['/subgroup/suboption1', '/subgroup/suboption2'], ('subgroup',))
    assert _resolve_default(root, Default({s1: s1}))  == ('/subgroup', ['/subgroup/suboption1', '/subgroup/suboption2'], ('subgroup',))

    # strings
    assert _resolve_default(root, Default('subgroup'))                 == ('/subgroup', ['/subgroup/suboption1', '/subgroup/suboption2'], ('subgroup',))
    assert _resolve_default(root, Default('/subgroup'))                == ('/subgroup', ['/subgroup/suboption1', '/subgroup/suboption2'], ('subgroup',))
    assert _resolve_default(root, Default(s1))                         == ('/subgroup', ['/subgroup/suboption1', '/subgroup/suboption2'], ('subgroup',))
    assert _resolve_default(root, Default(s1o1))                       == ('/subgroup', ['/subgroup/suboption1'], ('subgroup',))
    assert _resolve_default(root, Default({'/subgroup': 'suboption1'})) == ('/subgroup', ['/subgroup/suboption1'], ('subgroup',))
    assert _resolve_default(root, Default({'subgroup': 'suboption1'}))  == ('/subgroup', ['/subgroup/suboption1'], ('subgroup',))
    with pytest.raises(KeyError, match="Group '/subgroup2/subgroup3' does not have child 'subgroup'"):
        _resolve_default(s2s3, Default({'subgroup': 'suboption1'}))
    with pytest.raises(KeyError, match="Group '/subgroup2' does not have child 'subgroup'"):
        _resolve_default(s2,   Default({'subgroup': 'suboption1'}))
    with pytest.raises(KeyError, match="Group '/subgroup' does not have child 'subgroup'"):
        _resolve_default(s1,   Default({'subgroup': 'suboption1'}))


def test_defaults_advanced():

    def resolve_entry_defaults(group):
        results = []
        for default in group.get_option('default').get_unresolved_defaults():
            results.append(_resolve_default(group, default))
        return results

    assert resolve_entry_defaults(_make_config_group(suboption='suboption1')) == [('/subgroup', ['/subgroup/suboption1'], ('subgroup',))]
    assert resolve_entry_defaults(_make_config_group(suboption='suboption2')) == [('/subgroup', ['/subgroup/suboption2'], ('subgroup',))]
    assert resolve_entry_defaults(_make_config_group(suboption=['suboption2'])) == [('/subgroup', ['/subgroup/suboption2'], ('subgroup',))]
    assert resolve_entry_defaults(_make_config_group(suboption=['suboption1', 'suboption2'])) == [('/subgroup', ['/subgroup/suboption1', '/subgroup/suboption2'], ('subgroup',))]

    assert resolve_entry_defaults(_make_config_group(suboption=None, suboption2='suboption1')) == [('/subgroup2/subgroup3', ['/subgroup2/subgroup3/suboption1'], ('subgroup2', 'subgroup3'))]
    assert resolve_entry_defaults(_make_config_group(suboption=None, suboption2='suboption2')) == [('/subgroup2/subgroup3', ['/subgroup2/subgroup3/suboption2'], ('subgroup2', 'subgroup3'))]


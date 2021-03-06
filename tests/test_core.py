import pytest

from eunomia import eunomia, eunomia_runner, eunomia_load
from eunomia.backend import BackendObj, BackendDict
from eunomia.config.nodes import SubNode, EvalNode
from eunomia.config.nodes._nodes import OptNode
from tests.test_backend_obj import _make_config_group


# ========================================================================= #
# Test Eunomia                                                              #
# ========================================================================= #


def test_eunomia_loader_simple():
    eunomia_load(_make_config_group(suboption='suboption1', suboption2=None))
    eunomia_load(_make_config_group(suboption='suboption2', suboption2=None))
    eunomia_load(_make_config_group(suboption='suboption1', suboption2='suboption1'))
    eunomia_load(_make_config_group(suboption='suboption2', suboption2='suboption2'))
    eunomia_load(_make_config_group(suboption=None, suboption2='suboption1'))
    eunomia_load(_make_config_group(suboption=None, suboption2='suboption2'))


def test_eunomia_loader():
    # check no subgroups
    assert eunomia_load(_make_config_group(suboption=None)) == {'foo': 1}

    # test subgroup
    assert eunomia_load(_make_config_group(suboption='suboption1')) == {'subgroup': {'bar': 1}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption='suboption2')) == {'subgroup': {'bar': 2}, 'foo': 1}

    with pytest.raises(Exception):
        eunomia_load(_make_config_group(suboption='invalid___'))

    # test second subgroup
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='suboption1')) == {'foo': 1, 'subgroup': {'bar': 2}, 'subgroup2': {'subgroup3': {'baz': 1}}}
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='suboption2')) == {'foo': 1, 'subgroup': {'bar': 2}, 'subgroup2': {'subgroup3': {'baz': 2}}}

    # test root package
    assert eunomia_load(_make_config_group(suboption2='suboption2', package1='<root>')) == {'foo': 1, 'bar': 1, 'subgroup2': {'subgroup3': {'baz': 2}}}
    assert eunomia_load(_make_config_group(suboption2='suboption2', package2='<root>')) == {'foo': 1, 'subgroup': {'bar': 1}, 'baz': 2}

    # test package variations
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='suboption2', package1='<root>', package2='<root>')) == {'foo': 1, 'bar': 2, 'baz': 2}
    assert eunomia_load(_make_config_group(suboption='suboption1', suboption2='suboption2', package1='<root>', package2='<group>')) == {'foo': 1, 'bar': 1, 'subgroup2': {'subgroup3': {'baz': 2}}}
    assert eunomia_load(_make_config_group(suboption='suboption1', suboption2='suboption1', package1='<root>', package2='<option>')) == {'foo': 1, 'bar': 1, 'subgroup2': {'subgroup3': {'suboption1': {'baz': 1}}}}

    assert eunomia_load(_make_config_group(suboption='suboption1', suboption2='suboption1', package1='<group>', package2='<root>')) == {'foo': 1, 'subgroup': {'bar': 1}, 'baz': 1}
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='suboption2', package1='<group>', package2='<group>')) == {'foo': 1, 'subgroup': {'bar': 2}, 'subgroup2': {'subgroup3': {'baz': 2}}}
    assert eunomia_load(_make_config_group(suboption='suboption1', suboption2='suboption2', package1='<group>', package2='<option>')) == {'foo': 1, 'subgroup': {'bar': 1}, 'subgroup2': {'subgroup3': {'suboption2': {'baz': 2}}}}

    assert eunomia_load(_make_config_group(suboption='suboption1', suboption2='suboption2', package1='<option>', package2='<root>')) == {'foo': 1, 'subgroup': {'suboption1': {'bar': 1}}, 'baz': 2}
    assert eunomia_load(_make_config_group(suboption='suboption1', suboption2='suboption1', package1='<option>', package2='<group>')) == {'foo': 1, 'subgroup': {'suboption1': {'bar': 1}}, 'subgroup2': {'subgroup3': {'baz': 1}}}
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='suboption2', package1='<option>', package2='<option>')) == {'foo': 1, 'subgroup': {'suboption2': {'bar': 2}}, 'subgroup2': {'subgroup3': {'suboption2': {'baz': 2}}}}

    # test custom package
    assert eunomia_load(_make_config_group(suboption2='suboption2', package1='asdf', package2='fdsa.asdf')) == {'asdf': {'bar': 1}, 'fdsa': {'asdf': {'baz': 2}}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption2='suboption2', package1='asdf', package2='asdf.fdsa')) == {'asdf': {'bar': 1, 'fdsa': {'baz': 2}}, 'foo': 1}


def test_eunomia_loader_overrides():
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='suboption1')) == {'foo': 1, 'subgroup': {'bar': 2}, 'subgroup2': {'subgroup3': {'baz': 1}}}
    # change suboption2=suboption2
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='suboption1'), overrides=['/subgroup2/subgroup3/suboption2']) == {'foo': 1, 'subgroup': {'bar': 2}, 'subgroup2': {'subgroup3': {'baz': 2}}}
    # change suboption=suboption1 and suboption2=suboption2
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='suboption1'), overrides=['/subgroup2/subgroup3/suboption2', '/subgroup/suboption1']) == {'foo': 1, 'subgroup': {'bar': 1}, 'subgroup2': {'subgroup3': {'baz': 2}}}
    # check missing override
    with pytest.raises(KeyError, match='could not resolve the override'):
        eunomia_load(_make_config_group(suboption='suboption2', suboption2='suboption1'), overrides=['/subgroup2/subgroup3/suboption2', '/MALFORMED/suboption1'])
    # check unused override
    with pytest.raises(RuntimeError, match="the following overrides were not used to override defaults listed in the config: \\['/subgroup2/subgroup3']"):
        eunomia_load(_make_config_group(suboption='suboption2', suboption2=None), overrides=['/subgroup2/subgroup3/suboption2', '/subgroup/suboption1'])
    with pytest.raises(RuntimeError, match="the following overrides were not used to override defaults listed in the config: \\['/subgroup', '/subgroup2/subgroup3']"):
        eunomia_load(_make_config_group(suboption=None, suboption2=None), overrides=['/subgroup2/subgroup3/suboption2', '/subgroup/suboption1'])


def test_eunomia_loader_interpolation():
    # test custom packages with substitution
    with pytest.raises(TypeError, match='can never be a config node'):
        assert eunomia_load(_make_config_group(suboption2='suboption2', package1='asdf', package2=SubNode('asdf.fdsa')))

    # test interpolation values
    assert eunomia_load(_make_config_group(suboption=SubNode('suboption${=1}'))) == {'subgroup': {'bar': 1}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption=SubNode('f"suboption{1}"'))) == {'subgroup': {'bar': 1}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption=EvalNode('f"suboption{2}"'))) == {'subgroup': {'bar': 2}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption=SubNode('suboption${foo}'))) == {'subgroup': {'bar': 1}, 'foo': 1}

    # test option name references
    assert eunomia_load(_make_config_group(suboption='suboption1', suboption2=OptNode('/subgroup'))) == {'subgroup': {'bar': 1}, 'foo': 1, 'subgroup2': {'subgroup3': {'baz': 1}}}
    assert eunomia_load(_make_config_group(suboption='suboption1', suboption2=SubNode('${/subgroup}'))) == {'subgroup': {'bar': 1}, 'foo': 1, 'subgroup2': {'subgroup3': {'baz': 1}}}
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2=OptNode('/subgroup'))) == {'subgroup': {'bar': 2}, 'foo': 1, 'subgroup2': {'subgroup3': {'baz': 2}}}
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2=SubNode('${/subgroup}'))) == {'subgroup': {'bar': 2}, 'foo': 1, 'subgroup2': {'subgroup3': {'baz': 2}}}
    with pytest.raises(KeyError):
        eunomia_load(_make_config_group(suboption=SubNode('${/subgroup}'), suboption2='suboption2'))


def test_eunomia_core_funcs():

    root = _make_config_group()
    target = {'foo': 1, 'subgroup': {'bar': 1}}

    # LOADER

    # test group backend
    assert eunomia_load(root, 'default') == target
    assert eunomia_load(root, 'default', backend=BackendObj()) == target

    # test dict backend
    assert eunomia_load(BackendDict().dump(root), 'default') == target
    assert eunomia_load(BackendDict().dump(root), 'default', backend=BackendDict()) == target

    # RUNNERS

    def main(config):
        assert config == target
    eunomia_runner(main, root, 'default')
    eunomia_runner(main, root, 'default', backend=BackendObj())

    # WRAPPERS

    @eunomia(root, 'default')
    def main(config):
        assert config == target
    main()

    @eunomia(root, 'default', backend=BackendObj())
    def main(config):
        assert config == target
    main()



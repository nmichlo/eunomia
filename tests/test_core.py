import pytest

from eunomia import eunomia, eunomia_adv
from eunomia import eunomia_runner, eunomia_runner_adv
from eunomia import eunomia_load, eunomia_load_adv
from eunomia.backend import BackendObj, BackendDict
from eunomia.config.nodes import SubNode, EvalNode
from tests.test_backend_obj import _make_config_group


# ========================================================================= #
# Test Eunomia                                                              #
# ========================================================================= #


def test_eunomia_loader_simple():
    eunomia_load(_make_config_group(suboption='suboption1', suboption2=None))
    eunomia_load(_make_config_group(suboption='suboption2', suboption2=None))
    eunomia_load(_make_config_group(suboption='suboption1', suboption2='sub2option1'))
    eunomia_load(_make_config_group(suboption='suboption2', suboption2='sub2option2'))
    eunomia_load(_make_config_group(suboption=None, suboption2='sub2option1'))
    eunomia_load(_make_config_group(suboption=None, suboption2='sub2option2'))


def test_eunomia_loader():
    # check no subgroups
    assert eunomia_load(_make_config_group(suboption=None)) == {'foo': 1}

    # test subgroup
    assert eunomia_load(_make_config_group(suboption='suboption1')) == {'subgroup': {'bar': 1}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption='suboption2')) == {'subgroup': {'bar': 2}, 'foo': 1}

    with pytest.raises(Exception):
        eunomia_load(_make_config_group(suboption='invalid___'))

    # test second subgroup
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='sub2option1')) == {'foo': 1, 'subgroup': {'bar': 2}, 'subgroup2': {'subgroup3': {'baz': 1}}}
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='sub2option2')) == {'foo': 1, 'subgroup': {'bar': 2}, 'subgroup2': {'subgroup3': {'baz': 2}}}

    # test root package
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='<root>')) == {'foo': 1, 'bar': 1, 'subgroup2': {'subgroup3': {'baz': 2}}}
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package2='<root>')) == {'foo': 1, 'subgroup': {'bar': 1}, 'baz': 2}
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='<root>', package2='<root>')) == {'foo': 1, 'bar': 1, 'baz': 2}

    # test custom package
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='asdf', package2='fdsa.asdf')) == {'asdf': {'bar': 1}, 'fdsa': {'asdf': {'baz': 2}}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='asdf', package2='asdf.fdsa')) == {'asdf': {'bar': 1, 'fdsa': {'baz': 2}}, 'foo': 1}


def test_eunomia_loader_interpolation():
    # test custom packages with substitution
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='asdf', package2=SubNode('asdf.fdsa'))) == {'asdf': {'bar': 1, 'fdsa': {'baz': 2}}, 'foo': 1}

    # test interpolation values
    assert eunomia_load(_make_config_group(suboption=SubNode('suboption${=1}'))) == {'subgroup': {'bar': 1}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption=SubNode('f"suboption{1}"'))) == {'subgroup': {'bar': 1}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption=EvalNode('f"suboption{2}"'))) == {'subgroup': {'bar': 2}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption=SubNode('suboption${foo}'))) == {'subgroup': {'bar': 1}, 'foo': 1}


def test_eunomia_core_funcs():

    root = _make_config_group()
    target = {'foo': 1, 'subgroup': {'bar': 1}}

    # LOADER

    # test group backend
    assert eunomia_load(root, 'default') == target
    assert eunomia_load_adv(BackendObj(root), 'default') == target

    # test dict backend
    assert eunomia_load(root.to_dict(), 'default') == target
    assert eunomia_load_adv(BackendDict(root.to_dict()), 'default') == target

    # RUNNERS

    def main(config):
        assert config == target
    eunomia_runner(main, root, 'default')
    eunomia_runner_adv(main, BackendObj(root), 'default')

    # WRAPPERS

    @eunomia(root, 'default')
    def main(config):
        assert config == target
    main()
    @eunomia_adv(BackendObj(root), 'default')
    def main(config):
        assert config == target
    main()



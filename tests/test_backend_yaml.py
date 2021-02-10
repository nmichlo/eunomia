import pytest
from eunomia.backend._backend_yaml import yaml_load
from eunomia.config.nodes import IgnoreNode


# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def test_yaml_tags():
    assert yaml_load('1') == 1
    assert yaml_load('[1, 2, 3]') == [1, 2, 3]
    assert yaml_load('{1, 2, 3}') == {1: None, 2: None, 3: None}

    # string tag - only compatible with scalars
    assert yaml_load('!str f""') == IgnoreNode('f""')
    assert yaml_load('!str 1') == IgnoreNode('1')
    with pytest.raises(TypeError):
        assert yaml_load('!str {1, 2, 3}') == IgnoreNode('{1: None, 2: None, 3: None}')
    with pytest.raises(TypeError):
        assert yaml_load('!str [1, 2, 3]') == '[1, 2, 3]'

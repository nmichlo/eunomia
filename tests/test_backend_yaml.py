import pytest
from eunomia.backend._backend_yaml import yaml_load
from eunomia.config.nodes import InterpolateNode, IgnoreNode


# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def test_yaml_tags():
    assert yaml_load('1') == 1
    assert yaml_load('[1, 2, 3]') == [1, 2, 3]
    assert yaml_load('{1, 2, 3}') == {1: None, 2: None, 3: None}
    assert yaml_load('value: 1') == {InterpolateNode(value='value'): 1}

    # automatically add eval tag if string starts and ends like f-strings: f"..." or f'...'
    assert yaml_load('f""').get_config_value({}, {}, {}) == ''
    assert yaml_load('\'f""\'').get_config_value({}, {}, {}) == ''
    assert yaml_load('f"{1}"').get_config_value({}, {}, {}) == '1'
    assert yaml_load('f"{1}{[1,2]}"').get_config_value({}, {}, {}) == '1[1, 2]'
    assert yaml_load('f"{1}{[1,2]*2}"').get_config_value({}, {}, {}) == '1[1, 2, 1, 2]'
    assert yaml_load('f"| {\'=\'*5} |"').get_config_value({}, {}, {}) == '| ===== |'
    assert yaml_load('f"| {1+2+0.56:1.1f} |"').get_config_value({}, {}, {}) == '| 3.6 |'
    assert yaml_load('f"{round(0.5)}"').get_config_value({}, {}, {}) == '0'

    # string tag - only compatible with scalars
    assert yaml_load('!str f""') == IgnoreNode('f""')
    assert yaml_load('!str 1') == IgnoreNode('1')
    with pytest.raises(TypeError):
        assert yaml_load('!str {1, 2, 3}') == IgnoreNode('{1: None, 2: None, 3: None}')
    with pytest.raises(TypeError):
        assert yaml_load('!str [1, 2, 3]') == '[1, 2, 3]'

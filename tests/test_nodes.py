from eunomia.config.nodes import SubNode


def test_node_sub_fstrings():
    assert SubNode('f""').get_config_value({}, {}, {}) == ''
    assert SubNode('f"{1}"').get_config_value({}, {}, {}) == '1'
    assert SubNode('f"{1}{[1,2]}"').get_config_value({}, {}, {}) == '1[1, 2]'
    assert SubNode('f"{1}{[1,2]*2}"').get_config_value({}, {}, {}) == '1[1, 2, 1, 2]'
    assert SubNode('f"| {\'=\'*5} |"').get_config_value({}, {}, {}) == '| ===== |'
    assert SubNode('f"| {1+2+0.56:1.1f} |"').get_config_value({}, {}, {}) == '| 3.6 |'
    assert SubNode('f"{round(0.5)}"').get_config_value({}, {}, {}) == '0'

def test_node_sub():
    assert SubNode('a{1}b{2}c').get_config_value({},{},{}) == 'a{1}b{2}c'
    assert SubNode('a${=1}b${=2}c').get_config_value({},{},{}) == 'a1b2c'

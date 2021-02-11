import pytest

from eunomia import eunomia_load
from eunomia.backend import BackendObj, BackendDict, BackendYaml
from tests.test_backend_obj import _make_config_group
from tests.test_readme_examples import CONFIGS_DIR


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def test_simple_option():
    root = _make_config_group()

    # test group backend
    assert BackendObj(root).load_root_group().to_dict() == root.to_dict()
    with pytest.raises(TypeError, match='must be an instance of Group'):
        BackendObj(root.to_dict()).load_root_group().to_dict()

    # test dict backend
    assert BackendDict(root.to_dict()).load_root_group().to_dict() == root.to_dict()
    with pytest.raises(TypeError, match='must be a dict'):
        BackendDict(root).load_root_group().to_dict()

    # test yaml backend
    BackendYaml(CONFIGS_DIR).load_root_group()

    # test yaml backend
    merged = eunomia_load(CONFIGS_DIR, 'advanced')
    result = {
        'trainer': {'epochs': 100},
        'advanced': {
            'example_ref': 100,
            'example_ref_tag': 100,
            'example_expr': 200,
            'example_expr_tag': 200,
            'example_tuple': (100, 777),
            'example_tuple_tag': (100, 777),
            'example_fstr': '00100',
            'example_fstr_alt': '00100',
            'example_sub': 'prefix_[1, 2, 3]_suffix',
            'example_sub_tag': 'prefix_[1, 2, 3]_suffix',
            'example_sub_ignore': 'prefix_${=[1,2,3]}_suffix'
        },
        'framework': {
            '_target_': 'BetaVae', 'beta': 4
        },
        'dataset': {
            '_target_': 'Shapes3D', 'folder': './data/shapes3d'
        }
    }
    assert merged == result


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

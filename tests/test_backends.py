import pytest

from eunomia.backend import BackendObj, BackendDict, BackendYaml
from tests.test_backend_obj import _make_config_group
from tests.test_docs_examples import SIMPLE_CONFIG_DIR


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
    BackendYaml(SIMPLE_CONFIG_DIR).load_root_group()


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

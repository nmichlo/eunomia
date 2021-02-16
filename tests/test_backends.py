import pytest

from eunomia.backend import BackendObj, BackendDict, BackendYaml
from tests.test_backend_obj import _make_config_group
from tests.util import path_from_root


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def test_simple_option():
    root = _make_config_group()

    b_obj = BackendObj()
    b_dct = BackendDict()

    # test group backend
    assert b_obj.load_group(root).to_dict() == root.to_dict()
    with pytest.raises(TypeError, match='group value must be of type: .*Group'):
        b_obj.load_group(root.to_dict()).to_dict()

    # test dict backend
    assert b_dct.load_group(root.to_dict()).to_dict() == root.to_dict()
    with pytest.raises(TypeError, match='group value must be of type: .*dict'):
        b_dct.load_group(root).to_dict()

    # test yaml backend
    BackendYaml().load_group('examples/docs/quickstart/configs')


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

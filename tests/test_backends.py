import pytest

from eunomia.backend import BackendObj, BackendDict, BackendYaml
from tests.test_backend_obj import _make_config_group


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def test_simple_option():
    root = _make_config_group()

    b_obj = BackendObj()
    b_dct = BackendDict()

    # test group backend
    assert b_dct.dump(b_obj.load_group(root)) == b_dct.dump(root)
    with pytest.raises(TypeError, match='group value must be of type: .*Group'):
        b_dct.dump(b_obj.load_group(b_dct.dump(root)))

    # test dict backend
    assert b_dct.dump(b_dct.load_group(b_dct.dump(root))) == b_dct.dump(root)
    with pytest.raises(TypeError, match='group value must be of type: .*dict'):
        b_dct.dump(b_dct.load_group(root))

    # test yaml backend
    BackendYaml().load_group('examples/docs/quickstart/configs')


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

import pytest

from eunomia._util_attrdict import AttrDict


# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def check_dict_equal(a, b):
    # a, b = attrhelp.recursive_to_dict([a, b])
    assert a == b


def test_attrdict():
    conf = AttrDict({'a': {'b': {'a': 1}}})

    check_dict_equal(conf, {'a': {'b': {'a': 1}}})
    conf.a.b.a = 2
    check_dict_equal(conf, {'a': {'b': {'a': 2}}})
    conf.a.b.c = {'d': {'e': 3}}
    check_dict_equal(conf, {'a': {'b': {'a': 2, 'c': {'d': {'e': 3}}}}})
    conf.a.b.c.d.e = 4
    check_dict_equal(conf, {'a': {'b': {'a': 2, 'c': {'d': {'e': 4}}}}})

    with pytest.raises(AttributeError):
        invalid = conf.valid

    conf.valid = 42
    assert conf.valid == 42
    assert conf['valid'] == 42

    conf['valid'] = 7
    assert conf.valid == 7
    assert conf['valid'] == 7

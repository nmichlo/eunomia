import json
from eunomia.attrmap import AttrMap, attrhelp


# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def check_dict_equal(a, b):
    a, b = attrhelp.recursive_to_dict([a, b])
    assert a == b


def test_attrdict():
    conf = AttrMap({'a': {'b': {'a': 1}}})

    check_dict_equal(conf, {'a': {'b': {'a': 1}}})
    conf.a.b.a = 2
    check_dict_equal(conf, {'a': {'b': {'a': 2}}})
    conf.a.b.c = {'d': {'e': 3}}
    check_dict_equal(conf, {'a': {'b': {'a': 2, 'c': {'d': {'e': 3}}}}})
    conf.a.b.c.d.e = 4
    check_dict_equal(conf, {'a': {'b': {'a': 2, 'c': {'d': {'e': 4}}}}})

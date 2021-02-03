import pytest
from eunomia import eunomia_load
from eunomia.config import ConfigGroup, ConfigOption


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #
from eunomia.values import InterpolateValue, EvalValue


def _make_config_group(suboption='suboption1', suboption2=None, package1='_group_', package2='_group_') -> ConfigGroup:
    return ConfigGroup({
        'subgroup': ConfigGroup({
            'suboption1': ConfigOption({'_package_': package1, 'bar': 1}),
            'suboption2': ConfigOption({'_package_': package1, 'bar': 2}),
        }),
        'subgroup2': ConfigGroup({
            'sub2option1': ConfigOption({'_package_': package2, 'baz': 1}),
            'sub2option2': ConfigOption({'_package_': package2, 'baz': 2}),
        }),
        'default': ConfigOption({
            '_options_': {
                **({'subgroup': suboption} if suboption else {}),
                **({'subgroup2': suboption2} if suboption2 else {}),
            },
            'foo': 1
        }),
    })


def test_config_objects():
    _make_config_group(suboption='suboption1')
    _make_config_group(suboption='suboption2')
    _make_config_group(suboption='invalid___')  # invalid but not an error


# ========================================================================= #
# Test Eunomia                                                              #
# ========================================================================= #


def test_eunomia_loader():
    # check no subgroups
    assert eunomia_load(_make_config_group(suboption=None)) == {'foo': 1}

    # test subgroup
    assert eunomia_load(_make_config_group(suboption='suboption1')) == {'subgroup': {'bar': 1}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption='suboption2')) == {'subgroup': {'bar': 2}, 'foo': 1}
    with pytest.raises(Exception):
        eunomia_load(_make_config_group(suboption='invalid___'))

    # test second subgroup
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='sub2option1')) == {'subgroup': {'bar': 2}, 'subgroup2': {'baz': 1}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='sub2option2')) == {'subgroup': {'bar': 2}, 'subgroup2': {'baz': 2}, 'foo': 1}

    # test root package
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='_root_')) == {'bar': 1, 'subgroup2': {'baz': 2}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package2='_root_')) == {'subgroup': {'bar': 1}, 'baz': 2, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='_root_', package2='_root_')) == {'bar': 1, 'baz': 2, 'foo': 1}

    # test custom package
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='asdf', package2='fdsa.asdf')) == {'asdf': {'bar': 1}, 'fdsa': {'asdf': {'baz': 2}}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='asdf', package2='asdf.fdsa')) == {'asdf': {'bar': 1, 'fdsa': {'baz': 2}}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption2='sub2option2', package1='asdf', package2=InterpolateValue('${="asdf"}.fdsa'))) == {'asdf': {'bar': 1, 'fdsa': {'baz': 2}}, 'foo': 1}

    # test interpolation values
    assert eunomia_load(_make_config_group(suboption=InterpolateValue('suboption${=1}'))) == {'subgroup': {'bar': 1}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption=InterpolateValue('f"suboption{1}"'))) == {'subgroup': {'bar': 1}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption=EvalValue('f"suboption{2}"'))) == {'subgroup': {'bar': 2}, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption=InterpolateValue('suboption${foo}'))) == {'subgroup': {'bar': 1}, 'foo': 1}
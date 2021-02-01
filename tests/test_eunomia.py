import pytest
from eunomia import eunomia_load
from eunomia.backend import ConfigGroup, ConfigOption


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def _make_config_group(suboption='suboption1', suboption2=None) -> ConfigGroup:
    return ConfigGroup({
        'subgroup': ConfigGroup({
            'suboption1': ConfigOption({'bar': 1}),
            'suboption2': ConfigOption({'bar': 2}),
        }),
        'subgroup2': ConfigGroup({
            'sub2option1': ConfigOption({'baz': 1}),
            'sub2option2': ConfigOption({'baz': 2}),
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
    assert eunomia_load(_make_config_group(suboption='suboption1')) == {'bar': 1, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption='suboption2')) == {'bar': 2, 'foo': 1}
    with pytest.raises(Exception):
        eunomia_load(_make_config_group(suboption='invalid___'))
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='sub2option1')) == {'bar': 2, 'foo': 1}
    assert eunomia_load(_make_config_group(suboption='suboption2', suboption2='sub2option2')) == {'bar': 2, 'foo': 1}

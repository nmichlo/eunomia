import pytest
from eunomia.backend import ConfigGroup, ConfigOption


# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def test_config_nodes():

    a = ConfigGroup({
        'group_a': ConfigGroup({
            'option_a': ConfigOption({
                '_options_': {
                    'adsf': 'fdsa'
                }
            }),
            'option_b': ConfigOption({
                '_options_': {
                    'fdsa': 'asdf'
                }
            })
        }),

        'group_b': ConfigGroup({
            'option_c': ConfigOption({
                '_options_': {
                    'adsf': 'fdsa'
                }
            }),
            'option_d': ConfigOption({
                '_options_': {
                    'fdsa': 'asdf'
                }
            })
        })
    })


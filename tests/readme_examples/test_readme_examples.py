import os

# get the absolute path to the config dir relative to this file
CONFIGS_DIR = os.path.join(os.path.dirname(__file__), 'configs')

# the expected output
OUTPUT =\
"""
trainer:
  epochs: 100
framework:
  _target_: BetaVae
  beta: 4
dataset:
  _target_: Shapes3D
  folder: ./data/shapes3d
""".lstrip()


def test_readme_example_yaml():
    # ./main.py
    from eunomia import eunomia_load
    from ruamel import yaml

    config = eunomia_load(CONFIGS_DIR, 'default')
    # print(yaml.round_trip_dump(config))  # does not sort keys

    # >>> RESULT
    assert yaml.round_trip_dump(config) == OUTPUT


def test_readme_example_pythonic():
    from eunomia import eunomia_load
    from eunomia.config import Group, Option
    from ruamel import yaml

    group = Group({
        'framework': Group({
            'betavae': Option(data={
                '_target_': 'BetaVae',
                'beta': 4,
            })
        }),
        'dataset': Group({
            'shapes3d': Option(data={
                '_target_': 'Shapes3D',
                'folder': './data/shapes3d',
            })
        }),
        'default': Option(
            data={'trainer': {'epochs': 100}},
            opts={
                'framework': 'betavae',
                'dataset': 'shapes3d',
            }
        )
    })

    config = eunomia_load(group, 'default')
    # print(yaml.round_trip_dump(config))  # does not sort keys

    # >>> RESULT
    assert yaml.round_trip_dump(config) == OUTPUT

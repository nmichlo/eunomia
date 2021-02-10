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
    import yaml

    # replace configs './configs'
    config = eunomia_load(CONFIGS_DIR, 'default')
    # print(yaml.safe_dump(config, sort_keys=False))

    # >>> RESULT
    assert yaml.safe_dump(config, sort_keys=False) == OUTPUT


def test_readme_example_pythonic():
    from eunomia import eunomia_load
    from eunomia.config import Group, Option
    import yaml

    config_root = Group({
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

    config = eunomia_load(config_root, 'default')
    # print(yaml.safe_dump(config, sort_keys=False))

    # >>> RESULT
    assert yaml.safe_dump(config, sort_keys=False) == OUTPUT

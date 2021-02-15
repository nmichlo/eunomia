from eunomia import eunomia_load
from eunomia.config import Group, Option
from ruamel import yaml

group = Group({
    'framework': Group({
        'betavae': Option({
            '_target_': 'disent.frameworks.vae.unsupervised.BetaVae',
            'beta': 4,
        })
    }),
    'dataset': Group({
        'shapes3d': Option({
            '_target_': 'disent.data.groundtruth.Shapes3dData',
            'folder': '/tmp/data/shapes3d',
        })
    }),
    'default': Option(
        data={
            'trainer': {
                'epochs': 100
            }
        },
        defaults={
            'framework': 'betavae',
            'dataset': 'shapes3d',
        }
    )
})

config = eunomia_load(group, 'default')

# keys are ordered by insertion order
print(yaml.round_trip_dump(config), end='')

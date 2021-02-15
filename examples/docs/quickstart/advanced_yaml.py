from eunomia import eunomia_load
from ruamel import yaml

config = eunomia_load('./configs', 'advanced')

# keys are ordered by insertion order
print(yaml.round_trip_dump(config), end='')

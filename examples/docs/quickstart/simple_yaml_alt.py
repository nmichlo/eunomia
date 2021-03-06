from eunomia import eunomia_load
from ruamel import yaml

# changing the entry point gives as an example of why
# eunomia is so powerful! We can reuse options while
# only merging a subset of them.
config = eunomia_load('./configs', 'alternate')

# keys are ordered by insertion order
print(yaml.round_trip_dump(config), end='')

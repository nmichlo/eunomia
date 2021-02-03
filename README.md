# 📜 eunomia

> Eunomia, the Greek goddess of law and legislation. Directly translated as "good order" or "governance according to good laws"

Simple [hydra](https://github.com/facebookresearch/hydra) config like configuration
library supporting custom backends and variable interpolation.

Configs are defined as nested groups of mutually exclusive options
that can be selectively chosen.

## Docs (Coming Soon)

Have a look at the [docs and examples](https://eunomia.dontpanic.sh)!

## Why?

**Hydra Config Limitations:**
- Does not support custom backends
- Does not support nested pythonic config definitions
- Does not support simple python expressions
- Defaults are defined as lists not ordered dictionaries
- Uses custom yaml parsing to obtain package
- Config resolution order is unexpected (cannot reference config values in defaults lists)
- Overcomplicated / Depends on OmegaConf
- Release version 1.1 (with recursive defaults) was taking too long.

## Usage

### Terminology

We use the similar terminology to hydra config.
- Group: a mutually exclusive set of options (and other subgroups)
- Option: a selectable configuration dictionary

### Option Keys

Options are dictionaries that at their root can contain various special keys:
- `_package_`: (optional) `str` - Specify what the root of this chosen option should be after merging.
               Specify the package as fullstop `.` delimited keys. eg. `foo.bar.baz`.
    - Aliases exist:
        - `_root_` set the package as the root directory, ie. not placed in any key
        - `_group_` (default) set the package as the path to the current group that the option resides in.

- `_options_`: (optional) `dict[str, str]` - A dictionary of `subgroups` to `suboptions` that should also be merged.
               The group that the current option is in must contain the subgroup, that
               subgroup itself must contain the chosen suboption

- `_plugins_`: (optional) `dict[str, ?]` - Settings for various plugins. Can only be used if the package is `_root_`

### Merging

The merging process of configs is simple:
1. visit an option
2. merge the chosen option at the keys specified by `_package_`
3. recursively visit subgroup options in the order specified in `_options_` using depth first search.

## Yaml Example

Given the following configuration

```yaml
# ./configs/default.yaml
_options_:
  framework: betavae
  dataset: shapes3d
trainer:
  epochs: 100

# ./configs/framework/betavae.yaml
_target_: 'BetaVae'
beta: 4

# ./configs/dataset/shapes3d.yaml
_target_: 'Shapes3D'
folder: './data/shapes3d'
```

We can load the config by calling:

```python3
# ./main.py
from eunomia import eunomia_load
import yaml

if __name__ == '__main__':
    config = eunomia_load('./configs', 'default')
    print(yaml.safe_dump(config))
```

The resulting output of the merged config in yaml format is:

```yaml
trainer:
  epochs: 100
framework:
  _target_: 'BetaVae'
  beta: 4
dataset:
  _target_: 'Shapes3D'
  folder: './data/shapes3d'
```

## Pythonic Example

The above yaml configuration generates the following representation behind
the scenes using the yaml backend.

If we would prefer to specify everything manually we can use the
following equivalent pythonic nested approach:

```python3
# ./main.py
from eunomia import eunomia_load
from eunomia.config import ConfigGroup, ConfigOption
from pprint import pprint

config_root = ConfigGroup({
    'framework': ConfigGroup({
        'betavae': ConfigOption({
              '_target_': 'BetaVae',
              'beta': 4,
        })
    }),
    'dataset': ConfigGroup({
        'shapes3d': ConfigOption({
            '_target_': 'Shapes3D',
            'folder': './data/shapes3d',
        })
    }),
    'default': ConfigOption({
        '_options_': {
            'framework': 'betavae',
            'dataset': 'shapes3d',
        },
        'trainer': {
            'epochs': 100,
        }
    })
})

if __name__ == '__main__':
    config = eunomia_load(config_root, 'default')
    pprint(config)
```

The resulting output would be:

```python3
{
    'trainer': {
        'epochs': 100,
    },
    'framework': {
          '_target_': 'BetaVae',
          'beta': 4,
    },
    'dataset': {
        '_target_': 'Shapes3D',
        'folder': './data/shapes3d',
    }
}
```
from pprint import pprint
from typing import Iterator, Iterable

from eunomia._util_traverse import PyTransformer
from eunomia.values import BaseValue
from eunomia.backend import Backend, BackendConfigGroup
from eunomia.config._objects import ConfigOption, ConfigGroup
from eunomia.values._values import recursive_get_config_value_alt


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def dict_recursive_get(dct, keys: Iterable[str], make_missing=False):
    if not keys:
        return dct
    (key, *keys) = keys
    if make_missing:
        if key not in dct:
            dct[key] = {}
    return dict_recursive_get(dct[key], keys, make_missing=make_missing)


def dict_recursive_set(dct, keys: Iterable[str], value, make_missing=False):
    (key, *keys) = keys
    insert_at = dict_recursive_get(dct, keys, make_missing=make_missing)
    insert_at[key] = value


def _dict_recursive_update(left, right, stack):
    # right overwrites left
    for k, v in right.items():
        if k in left:
            if isinstance(left[k], dict) or isinstance(v, dict):
                new_stack = stack + [k]
                if not (isinstance(left[k], dict) and isinstance(v, dict)):
                    raise TypeError(f'Recursive update cannot merge keys with a different type if one is a dictionary. {".".join(new_stack)}')
                else:
                    _dict_recursive_update(left[k], v, stack=new_stack)
                    continue
        left[k] = v


def dict_recursive_update(left, right):
    _dict_recursive_update(left, right, [])


# ========================================================================= #
# Config Loader                                                             #
# ========================================================================= #


class ConfigLoader(object):

    def __init__(self, storage_backend: Backend):
        self._backend = storage_backend

    def load_config(self, config_name, return_merged_options=False):
        """
        flatten and merge the options lists using DFS, while
        simultaneously merging the config

        - When config dictionaries are encountered, those are also
          processed using DFS to obtain interpolated values, before
          being merged into the config.
            * Keys are not allowed to be interpolated values
        """

        merged_options = {}
        merged_config = {}

        def _dfs_options(option: ConfigOption):
            assert isinstance(option, ConfigOption)
            group = option.parent
            assert isinstance(group, ConfigGroup)
            # process all sub_groups
            for subgroup_key, suboption_key in option.options.items():
                subgroup = group.get_subgroup(subgroup_key)
                suboption = subgroup.get_option(suboption_key)  # TODO: variable interpolation is not available here...
                _handle_option(suboption)

        def _merge_options(option: ConfigOption):
            # get the path to the config - recursive version of whats listed in the _options_
            # maybe lift the non-recursive limitation in future?
            group_path = option.group_path
            # check that this is not a duplicate
            if group_path in merged_options:
                prev_added_path = merged_options[group_path]
                raise KeyError(f'Group has duplicate entry: {repr(group_path)}. '
                               f'Key previously added by: {repr(prev_added_path)}. '
                               f'Current config file is: {repr(option.path)}.')
            # merge the path!
            merged_options[group_path] = option.path

        def _merge_config(option: ConfigOption):
            # merge the config into merged_config
            # make sure that interpolated values are available
            # TODO: dfs here should be synchronised with all values,
            #       as soon as one is encountered and merged, they should
            #       be available for future values.
            dict_recursive_update(
                left=dict_recursive_get(merged_config, option.package.keys, make_missing=True),
                right=recursive_get_config_value_alt(
                    merged_config=merged_config,
                    merged_options=merged_options,
                    current_config=option.config,
                    value=option.config
                )
            )

        def _handle_option(option: ConfigOption):
            # TODO: fix resolving of variables
            # TODO: add _plugins_ support
            _merge_options(option)
            _merge_config(option)
            _dfs_options(option)

        # entry point for dfs
        root_group = self._backend.load_root_group()
        entry_option = root_group.get_option(config_name)
        _handle_option(entry_option)

        # done, return the result
        if return_merged_options:
            return merged_config, merged_options
        return merged_config


# ========================================================================= #
# End                                                                       #
# ========================================================================= #


if __name__ == '__main__':
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

    loader = ConfigLoader(BackendConfigGroup(_make_config_group(
        suboption='suboption1',
        suboption2='sub2option1',
    )))

    conf, opts = loader.load_config('default', return_merged_options=True)
    print('=======')
    pprint(opts, sort_dicts=False)
    print('=======')
    pprint(conf, sort_dicts=False)

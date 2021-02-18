from typing import Tuple

from eunomia.util._util_dict import recursive_getitem, dict_recursive_update
from eunomia.config import Option, Group
from eunomia.config.nodes import ConfigNode

from eunomia.config import keys as K
from eunomia.config import validate as V


# ========================================================================= #
# Config Loader                                                             #
# ========================================================================= #


class ConfigLoader(object):

    def __init__(self, root_group: Group, overrides: list = None):
        # check root group
        if not isinstance(root_group, Group):
            raise TypeError(f'root_group must be a {Group.__name__}')
        self._root_group = root_group
        # merged items
        self._merged_options = None
        self._merged_config = None
        # make defaults overrides
        self._overrides = V.normalise_overrides(overrides)
        self._overridden = {}

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Checks                                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _pre_merge_checks(self):
        # 2.1 check all overrides exist in config
        if self._overrides:
            for group_keys, opt_name in self._overrides.items():
                if not self._root_group.has_option_recursive(group_keys + (opt_name,)):
                    raise KeyError(f'specified override does not exist in the config: {V.keys_as_abs_config_path(group_keys + (opt_name,))}')

    def _post_merge_checks(self):
        # ===================== #
        # all values have not yet been resolved in the merge config!
        # ===================== #
        # 2.3 make sure all overrides were used!
        if self._overrides:
            unused_overrides = set(self._overrides.keys()) - set(self._overridden.keys())
            if unused_overrides:
                raise RuntimeError(
                    f'the following overrides were not used to override defaults listed in the config: {sorted(map(V.keys_as_abs_config_path, unused_overrides))}')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Core Algorithm                                                        #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def load_config(self, config_name, return_merged_options=False):
        """
        flatten and merge the options lists using DFS, while
        simultaneously merging the config

        - When config dictionaries are encountered, those are also
          processed using DFS to obtain substituted values, before
          being merged into the config.
            * Keys are not allowed to be substituted values
        """
        self._merged_options = {}
        self._merged_config = {}

        # ===================== #
        # 1. entry point for dfs, get initial option
        entry_option = self._root_group.get_option(config_name)
        # ===================== #
        # 2.1. pre checks
        self._pre_merge_checks()
        # 2.2. perform dfs & merging and finally resolve values
        self._visit_option(entry_option)
        # 2.3 post checks
        self._post_merge_checks()
        # ===================== #
        # 3. finally resolve all the values in the config
        self._resolve_all_values()
        # ===================== #

        # done, return the result
        if return_merged_options:
            return self._merged_config, self._merged_options
        return self._merged_config

    def _visit_option(self, option: Option):
        # ===================== #
        # 1. check where to process self, and make sure self is in the options list
        # by default we want to merge this before children so we can reference its values.
        defaults = option.get_unresolved_defaults()
        if K.OPT_SELF not in defaults:
            # allow referencing parent values in children
            defaults = [K.OPT_SELF] + defaults
            # allow parent overwriting children values
            # group_paths = group_paths + [s.OPT_SELF]
        self_has_been_handled = False
        # ===================== #
        # 2. process options in order
        for default_item in defaults:
            # handle different cases
            if default_item == K.OPT_SELF:
                # ===================== #
                if self_has_been_handled:
                    raise RuntimeError(f'{K.OPT_SELF} was encountered more than once in option: {option.abs_path}')
                self_has_been_handled = True
                # 2.a if self is encountered, merge into config. We skip the
                #     value of the option_name here as it is not needed.
                self._merge_option(option)
                # ===================== #
            else:
                # normalise the default, can be strings, dicts, options, config nodes, tuples -> Union[Tuple[str, str], K.OPT_SELF]
                group_path, option_name = self._resolve_default_item(default_item)
                # ===================== #
                # allow groups/options to be overridden
                if self._overrides:
                    # get the absolute keys to the group
                    orig_group_keys: Tuple[str] = option.group.path_to_abs_keys(group_path)
                    if orig_group_keys in self._overrides:
                        # make sure it has not been overridden before
                        if orig_group_keys in self._overridden:
                            raise RuntimeError(f'default entry for group: {option.group.abs_path} has already been overridden: "{orig_group_keys}: {orig_option_name}"')
                        self._overridden[orig_group_keys] = option_name
                        option_name = self._overrides[orig_group_keys]
                # ===================== #
                # 2.b dfs through options
                # supports relative & absolute paths
                group = option.group.get_group_recursive(group_path, make_missing=False)
                # visit the next option
                self._visit_option(group.get_option(option_name))
                # ===================== #

    def _merge_option(self, option: Option):
        # TODO: this should have different modes
        #       - do not allow from the same group to be merged
        #       - allow from the same group to be merged
        #       - only replace existing values on lhs, don't merge
        #       - only add missing values on lhs, don't merge or replace
        # ===================== #
        # 1. check that the group that the option belongs to has not already been merged.
        #    Then mark the group the option belongs to as visited
        # ===================== #
        # check that this is not a duplicate
        group_keys = option.group_keys
        if group_keys in self._merged_options:
            prev_added_keys = self._merged_options[group_keys]
            raise KeyError(f'Group has duplicate entry: {repr(group_keys)}. '
                           f'Key previously added by: {repr(prev_added_keys)}. '
                           f'Current config file is: {repr(option.keys)}.')
        # mark group as visited
        self._merged_options[group_keys] = option.keys
        # ===================== #
        # 2. merged the data
        # ===================== #
        # 2.1. get the package and handle special values
        keys = self._resolve_package(option)
        # 2.2. get the root config object according to the package
        root = recursive_getitem(self._merged_config, keys, make_missing=True)
        # 2.3. merge the option into the config
        dict_recursive_update(left=root, right=option.get_unresolved_data(), allow_overwrite=False)
        # ===================== #

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Resolving Values                                                      #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _resolve_default_item(self, default_item):
        # split the default item
        result = V.split_defaults_item(
            self._resolve_value(default_item),
            allow_config_node_return=True,
        )
        # handle the case where an option instance was in the list
        if isinstance(result, Option):
            group_path, option_name = result.abs_group_path, result.key
        elif result == K.OPT_SELF:
            raise RuntimeError('This is a bug')
        else:
            group_path, option_name = result
        # check that the components are valid
        return V.validate_resolved_defaults_item(
            self._resolve_value(group_path),
            self._resolve_value(option_name),
        )

    def _resolve_value(self, value):
        # 1. allow interpolation of config objects
        # 2. TODO: process dictionary syntax with _node_ keys
        if isinstance(value, ConfigNode):
            value = value.get_config_value(self._merged_config, self._merged_options, {})
        return value

    def _resolve_package(self, option) -> Tuple[str]:
        path = self._resolve_value(option.get_unresolved_package())
        # check the type
        if not isinstance(path, str):
            raise TypeError(f'{K.KEY_PKG} must be a string')
        # handle special values
        if path == K.PKG_ROOT:
            keys = ()
        elif path == K.PKG_GROUP:
            keys = option.group_keys
        else:
            keys, is_relative = V.split_package_path(path)
            if is_relative:
                keys = option.group_keys + keys
        # return the keys
        return keys

    def _resolve_all_values(self):
        # TODO: this is wrong!
        # TODO: config is not mutated on the fly, cannot substitute chains of values.
        self._merged_config = ConfigNode.recursive_get_config_value(
            self._merged_config,
            self._merged_options,
            {},
            self._merged_config
        )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # END Loader                                                            #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

from typing import Tuple, List, Union, Optional

from eunomia.config._default import Default
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
        # has_run
        self._has_run = False
        # merged items
        self._merged_options = {}
        self._first_merge_from = {}
        self._merged_config = {}
        # make defaults overrides
        self._overrides = self._resolve_overrides_list(overrides)
        self._overridden = {}
        # debug
        self._debug = False
        self._debug_depth = 0

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Checks                                                                #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _pre_merge_checks(self):
        # 2.1 check all overrides exist in config
        # NOT NEEDED BECAUSE OF OVERRIDE RESOLVER
        # if self._overrides:
        #     for group_keys, (o_grp, o_opts) in self._overrides.items():
        #         for opt in o_opts:
        #             if not self._root_group.has_option_recursive(group_keys + (opt.key,)):
        #                 raise KeyError(f'specified override does not exist in the config: {V.keys_as_abs_config_path(group_keys + (opt.key,))}')
        pass

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

    def load_config(self, config_name, return_merged_options=False) -> Union[dict, Tuple[dict, dict]]:
        """
        flatten and merge the options lists using DFS, while
        simultaneously merging the config

        - When config dictionaries are encountered, those are also
          processed using DFS to obtain substituted values, before
          being merged into the config.
            * Keys are not allowed to be substituted values
        """
        # ===================== #
        # make sure we cant run the loader more than once
        if self._has_run:
            raise RuntimeError('Loader cannot be run more than once!')
        self._has_run = True
        # ===================== #
        # 1. entry point for dfs, get initial option
        entry_option = self._root_group.get_option(config_name)
        if self._debug:
            print(f'\nentrypoint: {repr(entry_option.abs_path)}')
        # ===================== #
        # 2.1. pre checks
        self._pre_merge_checks()
        # 2.2. perform dfs & merging and finally resolve values
        self._visit_option(entry_option, parent_option=None)
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

    def _visit_option(self, option: Option, parent_option: Optional[Option]):
        if self._debug:
            print(f'{" "*self._debug_depth*4}> visiting {repr(option.abs_path)} from {repr(parent_option.abs_path) if parent_option else "<user>"}')
            self._debug_depth += 1
        # ===================== #
        # 1. check where to process self, and make sure self is in the options list
        # by default we want to merge this before children so we can reference its values.
        handled_defaults = set()
        defaults = option.get_unresolved_defaults()
        if not any(default.is_self_pre_resolve for default in defaults):
            # allow referencing parent values in children
            defaults = [Default.make_self()] + defaults
            # allow parent overwriting children values
            # group_paths = group_paths + [s.OPT_SELF]
        # ===================== #
        # 2. process options in order
        for default in defaults:
            # normalise the default
            # -- various different objects as well as substitution need to be handled
            d_obj, d_options, d_pkg_keys, d_is_self = default.to_resolved_components(option, resolver=self._resolve_value)
            if self._debug:
                print(f'{" " * self._debug_depth * 4}? resolved default { {d_obj.abs_path: [o.key for o in d_options]} } from {default._default}')
            # ===================== #
            # make sure that self is only ever handled once
            key = K.OPT_SELF if d_is_self else V.keys_as_abs_config_path(d_obj.keys)
            if key in handled_defaults:
                raise RuntimeError(f'resolved default {key} was encountered more than once in option: {option.abs_path}')
            handled_defaults.add(key)
            # ===================== #
            # handle different cases
            if d_is_self:
                # ===================== #
                # 2.a if self is encountered, merge into config. We skip the
                #     value of the option_name here as it is not needed.
                self._merge_option(*d_options, pkg_keys=d_pkg_keys, parent_option=parent_option)
                # ===================== #
            else:
                # ===================== #
                # allow groups/options to be overridden
                o_obj, o_options = self._resolve_override(option, d_obj, d_options)
                if o_obj is not d_obj:
                    raise AssertionError('this should never happen. overridden default options come from different group.')
                # ===================== #
                # 2.b dfs through options
                # visit the next option
                for o_option in o_options:
                    self._visit_option(o_option, parent_option=option)
                # ===================== #
        if self._debug:
            self._debug_depth -= 1

    def _merge_option(self, option: Option, pkg_keys: Tuple[str], parent_option: Optional[Option]):
        # TODO: this should have different modes
        #       - do not allow from the same group to be merged
        #       - allow from the same group to be merged
        #       - only replace existing values on lhs, don't merge
        #       - only add missing values on lhs, don't merge or replace
        # ===================== #
        # 1. check that the group that the option belongs to has not already been merged.
        #    Then mark the group the option belongs to as visited
        #    - if the same source is still merging an option, then we allow
        #      it even if there are multiple
        # ===================== #
        # the path to the group containing the option being merged
        group_keys = option.group_keys
        # the parent option can merge one or more options from the above group
        # once a parent option has been set, being the first to encounter a default, a
        # different parent option cannot merge options from the same group.
        first_merge_from = self._first_merge_from.setdefault(group_keys, parent_option if parent_option else None)  # none means the user!
        visitor = "<user>" if first_merge_from is None else repr(first_merge_from.abs_group_path)
        if first_merge_from is not parent_option:
            raise RuntimeError(f'The first merge of options from the group {repr(option.abs_group_path)} occurred '
                               f'from {visitor} a different parent option cannot request a merge: {repr(option.abs_group_path)}')
        # check that this exact option has not been visited before
        if group_keys in self._merged_options:
            if option.key in self._merged_options[group_keys]:
                raise KeyError(f'option {repr(option.abs_path)} was previously visited by {visitor}')
        # mark group as visited
        self._merged_options.setdefault(group_keys, []).append(option.key)
        # ===================== #
        # 2. merged the data
        # ===================== #
        # 2.1. get the root config object according to the package
        root = recursive_getitem(self._merged_config, pkg_keys, make_missing=True)
        # 2.2. merge the option into the config
        data = option.get_unresolved_data()
        dict_recursive_update(left=root, right=data, allow_overwrite=True)
        # ===================== #
        if self._debug:
            print(f'{" "*self._debug_depth*4}* merged data from {repr(option.abs_path)} into output config at {pkg_keys}')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Resolving Values                                                      #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def _resolve_override(self, option: Option, d_obj: Union[Group, Option], d_options: List[Option]) -> Tuple[Union[Group, Option], List[Option]]:
        # if there is no listed override, return the usual options to merge
        d_group_keys = d_obj.group_keys
        if d_group_keys not in self._overrides:
            return d_obj, d_options
        # make sure it has not been overridden before
        if d_group_keys in self._overridden:
            raise RuntimeError(f'default lists entry for group: {option.abs_group_path} has already been overridden: "{d_obj.abs_group_path}: {tuple(o.key for o in d_options)}"')
        self._overridden[d_group_keys] = (d_obj, d_options)
        # if there is an override, return the override
        return self._overrides[d_group_keys]

    def _resolve_overrides_list(self, overrides: list) -> dict:
        if overrides is None:
            return {}
        # resolve overrides
        overrides_dct = {}
        for override in overrides:
            o = Default(override)
            if o.is_self_pre_resolve:
                raise KeyError(f'override cannot be self: {repr(override)}')
            try:
                o_obj, o_options, _, o_is_self = o.to_resolved_components(self._root_group, resolver=None, force_substitute=False)
            except KeyError as e:
                raise KeyError(f'could not resolve the override {repr(override)}, are you sure it exists in the config tree?').with_traceback(e.__traceback__)
            if o_is_self:
                raise KeyError(f'override cannot resolve to self: {repr(override)}')
            overrides_dct[o_obj.group_keys] = (o_obj, o_options)
        # return!
        return overrides_dct

    def _resolve_value(self, value):
        # 1. allow interpolation of config objects
        # 2. TODO: process dictionary syntax with _node_ keys
        if isinstance(value, ConfigNode):
            value = value.get_config_value(self._merged_config, self._merged_options, {})
        return value

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

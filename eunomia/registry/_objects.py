import inspect
import os
import re
from collections import defaultdict
from typing import Dict, Union, DefaultDict, List, Tuple, Optional

from eunomia.config import Group, Option
from eunomia.config import scheme as s


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def _get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }

def _get_module_path(obj):
    path = os.path.relpath(inspect.getmodule(obj).__file__, os.getcwd())
    assert path.endswith('.py')
    path = path[:-len('.py')]
    return os.path.normpath(path)


def _get_import_path(obj):
    module_path = '.'.join(_get_module_path(obj).split('/'))
    return f'{module_path}.{obj.__name__}'


def _camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


# ========================================================================= #
# Advanced Group                                                            #
# ========================================================================= #


class RegistryGroup(Group):

    """
    This group allows registration of functions or classes, constructing an
    option that has the _target_ parameter set, with default values obtained
    from the default parameters of the function.

    The option by default resides under the group that corresponds to the module
    that the function or class resides in.
    """

    def __init__(
            self,
            named_nodes: Dict[str, Union['Group', 'Option']] = None,
    ):
        super().__init__(named_nodes=named_nodes)
        # save all included options
        self._registered_all: DefaultDict[object, List[Option]] = defaultdict(list)
        self._registered_defaults: Dict[object, Tuple[bool, Option]] = {}

    def register(self, option_name: str = None, group_path: str = None, target: str = None, override_defaults=None, is_default=None):
        assert not self.has_parent, 'Can only register on the root node.'
        # wrap!
        def wrapper(func):
            # get the function paths
            import_path = _get_import_path(func) if target is None else target
            module_path = _get_module_path(func) if group_path is None else group_path
            # construct option
            overrides = override_defaults if override_defaults else {}
            kwargs = _get_default_args(func)
            for k in kwargs:
                if k in overrides:
                    kwargs[k] = overrides.pop(k)
            assert not overrides, f'tried to override missing values: {list(overrides.keys())}'
            assert s.MARKER_KEY_TARGET not in kwargs, f'object {import_path} has conflicting optional parameter: {s.MARKER_KEY_TARGET}'
            # get group and make missing along path
            group = self.get_group_from_path(path=module_path, make_missing=True)
            # get the name of the option from the function
            option_key = _camel_to_snake(func.__name__) if option_name is None else option_name
            # register the option
            option = group.add_option(option_key, Option(data={
                s.MARKER_KEY_TARGET: import_path,
                **kwargs
            }))
            self._register_obj(func, option, is_default)
            # return the original function
            return func

        # decorate correctly!
        if callable(group_path):
            fn, group_path = group_path, None
            return wrapper(fn)
        else:
            return wrapper

    def _register_obj(self, func, option, is_default=None):
        assert not self.has_parent, 'Can only register on the root node.'
        # keep track that this was registered
        self._registered_all[func].append(option)
        # register as a default
        if func in self._registered_defaults:
            explicit, _ = self._registered_defaults[func]
            if explicit:
                if is_default:
                    raise AssertionError(f'registered callable {func} for option: {option.keys} was previously explicitly registered as a default.')
            else:
                if is_default:
                    self._registered_defaults[func] = (True, option)
                elif is_default is None:
                    self._registered_defaults.setdefault(func, (False, option))
        else:
            if is_default or (is_default is None):
                self._registered_defaults.setdefault(func, (False if is_default is None else True, option))

    def get_registered_defaults(self, explicit_only=False):
        assert not self.has_parent, 'Can only register on the root node.'
        # get include!
        defaults = {}
        for func, (explicit, option) in self._registered_defaults.items():
            if explicit_only and not explicit:
                continue
            k = option.group_path
            if k in defaults:
                raise AssertionError(f'default for callable {func} corresponding to option: {option.keys} has already been added.')
            defaults[k] = option.key
        return defaults

# ========================================================================= #
# END                                                                       #
# ========================================================================= #


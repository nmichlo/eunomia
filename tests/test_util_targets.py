import itertools

import pytest

from eunomia.backend import BackendDict
from eunomia.config import Group, Option
from eunomia.util._targets import call, instantiate, import_module_attr
import ruamel
import math


def test_import_objects():
    assert import_module_attr('dict') is dict
    assert import_module_attr('list') is list

    assert import_module_attr('math.log') is math.log

    assert import_module_attr('ruamel.yaml') is ruamel.yaml  # odd one
    assert import_module_attr('ruamel.yaml.round_trip_dump') is ruamel.yaml.round_trip_dump  # odd one

    assert import_module_attr('eunomia.config.Group') is Group
    assert import_module_attr('eunomia.config.Option') is Option
    assert import_module_attr('eunomia.config.Group.has_suboption') is Group.has_suboption
    assert import_module_attr('eunomia.config.Option.get_child') is Option.get_child

    with pytest.raises(ValueError, match='must contain at least one module component'):
        import_module_attr('')
    with pytest.raises(AttributeError, match="could not import target 'math'. module 'builtins' has no attribute 'math'"):
        import_module_attr('math')
    with pytest.raises(AttributeError, match="could not import target 'math.asdf'. module 'math' has no attribute 'asdf'"):
        import_module_attr('math.asdf')
    with pytest.raises(AttributeError, match="could not import target 'math.log.asdf'. 'builtin_function_or_method' object has no attribute 'asdf'"):
        import_module_attr('math.log.asdf')
    with pytest.raises(AttributeError, match="could not import target 'eunomia.config.Option.asdf'. type object 'Option' has no attribute 'asdf'"):
        import_module_attr('eunomia.config.Option.asdf')
    with pytest.raises(ImportError, match="could not import target 'eunomiaINVALID.config.Option.get_child'. Are you sure the import module is correct?"):
        import_module_attr('eunomiaINVALID.config.Option.get_child')

def test_instantiate_targets():
    # check that the functions are the same, just nice to indicate whats going on
    assert call is instantiate

    # check basic instantiate
    assert isinstance(instantiate({'_target_': 'eunomia.config.Group'}, recursive=True, ensure_root_target=True), Group)
    assert isinstance(instantiate({'_target_': 'eunomia.config.Option'}, recursive=True, ensure_root_target=False), Option)
    assert isinstance(instantiate({'_target_': 'eunomia.config.Group'}, recursive=False, ensure_root_target=True), Group)
    assert isinstance(instantiate({'_target_': 'eunomia.config.Option'}, recursive=False, ensure_root_target=False), Option)

    bk = BackendDict()
    # check recursive instantiate
    option = Option(data={'foo': 1}, pkg='pkg.subpkg', defaults=[('group', 'subgroup')])
    option_target = {'_target_': 'eunomia.config.Option', '_args_': [dict(foo=1), 'pkg.subpkg', ['group/subgroup']]}
    # check no recursive elements
    assert bk.dump(instantiate(option_target, recursive=True, ensure_root_target=True)) == bk.dump(option)
    assert bk.dump(instantiate(option_target, recursive=True, ensure_root_target=False)) == bk.dump(option)
    assert bk.dump(instantiate(option_target, recursive=False, ensure_root_target=True)) == bk.dump(option)
    assert bk.dump(instantiate(option_target, recursive=False, ensure_root_target=False)) == bk.dump(option)
    # check wrong base element
    # -- no recursive
    assert instantiate([option_target], recursive=False, ensure_root_target=False) == [option_target]
    assert instantiate({'asdf': option_target}, recursive=False, ensure_root_target=False) == {'asdf': option_target}
    # -- no recursive -- strict
    with pytest.raises(TypeError, match='Could not instantiate root object: not a dictionary'):
        instantiate([option_target], recursive=False, ensure_root_target=True)
    with pytest.raises(KeyError, match="Could not instantiate root object: target marker key '_target_' not found in root"):
        instantiate({'asdf': option_target}, recursive=False, ensure_root_target=True)

    # check advanced recursive instantiate
    group = Group({'default': option})
    group_target = {'_target_': 'eunomia.config.Group', '_args_': [{'default': option_target}]}
    group_target_WRONG = {'_target_': 'eunomia.config.Option', '_args_': [{'default': option_target}]}
    # checks wrong call!
    with pytest.raises(RuntimeError, match="Could not call target 'eunomia.config.Option' object <class"):
        instantiate(group_target_WRONG, recursive=True, ensure_root_target=True)
    # checks recursive call
    assert bk.dump(instantiate(group_target, recursive=True, ensure_root_target=True)) == bk.dump(group)

    # check advanced recursive instantiate
    option_alt = Option(data={'foo': 1}, pkg='pkg.subpkg', defaults=[('group', 'subgroup')])
    # args, kwargs key mix
    option_target_alt1 = {'_target_': 'eunomia.config.Option', '_args_': [dict(foo=1), 'pkg.subpkg', ['group/subgroup']]}
    option_target_alt2 = {'_target_': 'eunomia.config.Option', '_args_': [dict(foo=1), 'pkg.subpkg'], '_kwargs_': dict(defaults=['group/subgroup'])}
    option_target_alt3 = {'_target_': 'eunomia.config.Option', '_args_': [dict(foo=1)], '_kwargs_': dict(pkg='pkg.subpkg', defaults=['group/subgroup'])}
    option_target_alt4 = {'_target_': 'eunomia.config.Option', '_kwargs_': dict(data=dict(foo=1), pkg='pkg.subpkg', defaults=['group/subgroup'])}
    assert bk.dump(instantiate(option_target_alt1)) == bk.dump(option_alt)
    assert bk.dump(instantiate(option_target_alt2)) == bk.dump(option_alt)
    assert bk.dump(instantiate(option_target_alt3)) == bk.dump(option_alt)
    assert bk.dump(instantiate(option_target_alt4)) == bk.dump(option_alt)
    # args, root kwargs mix
    option_target_alt1 = {'_target_': 'eunomia.config.Option', '_args_': [dict(foo=1), 'pkg.subpkg'], 'defaults': ['group/subgroup']}
    option_target_alt2 = {'_target_': 'eunomia.config.Option', '_args_': [dict(foo=1)], 'pkg': 'pkg.subpkg', 'defaults': ['group/subgroup']}
    option_target_alt3 = {'_target_': 'eunomia.config.Option', 'data': dict(foo=1), 'pkg': 'pkg.subpkg', 'defaults': ['group/subgroup']}
    option_target_alt4 = {'_target_': 'eunomia.config.Option', 'data': dict(foo=1), 'pkg': 'pkg.subpkg', '_kwargs_': dict(defaults=['group/subgroup'])}
    assert bk.dump(instantiate(option_target_alt1)) == bk.dump(option_alt)
    assert bk.dump(instantiate(option_target_alt2)) == bk.dump(option_alt)
    assert bk.dump(instantiate(option_target_alt3)) == bk.dump(option_alt)
    with pytest.raises(KeyError, match="target dictionary contains the _kwargs_ key as well as unused keys"):
        assert bk.dump(instantiate(option_target_alt4)) == bk.dump(option_alt)

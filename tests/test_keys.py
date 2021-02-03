import pytest

from eunomia.config import ConfigGroup, ConfigOption
from eunomia.config.keys import KEY_GROUP, KEY_PACKAGE, KEY_OPTIONS, KEY_PLUGINS
from eunomia.config.keys import Key, InsideGroupKey, InsideOptionKey, GroupKey, PkgKey
from eunomia.config.keys import Path, PkgPath, GroupPath


# ========================================================================= #
# Test Config Keys                                                          #
# ========================================================================= #


def test_eunomia_keys():

    Key('asdf')
    Key('_asdf')
    Key('_asdf_')
    Key(Key('_asdf_'))

    Key(KEY_PACKAGE)
    Key(KEY_OPTIONS)

    # package directive check
    with pytest.raises(ValueError): Key(PkgPath.PKG_ALIAS_GROUP)
    with pytest.raises(ValueError): Key(PkgPath.PKG_ALIAS_ROOT)

    # type check
    with pytest.raises(TypeError): Key(123)
    with pytest.raises(TypeError): Key(['asdf'])

    # invalid names check
    with pytest.raises(ValueError): Key('asdf.fdsa')
    with pytest.raises(ValueError): Key('1234')

    # keywords check
    with pytest.raises(ValueError): Key('global')
    with pytest.raises(ValueError): Key('is')

    # dict check -- TODO: maybe remove? This is very limiting.
    with pytest.raises(ValueError): Key('items')
    with pytest.raises(ValueError): Key('update')
    with pytest.raises(ValueError): Key('values')
    with pytest.raises(ValueError): Key('keys')


def test_eunomia_packages():

    # check instantiation
    PkgPath('asdf')
    PkgPath('asdf.fdsa')
    PkgPath(['asdf', 'fdsa'])
    PkgPath(('asdf', 'fdsa'))
    PkgPath('_asdf')
    PkgPath('_asdf_')

    PkgPath('valid')
    PkgPath('valid.valid')

    with pytest.raises(ValueError): PkgPath('1invalid')
    with pytest.raises(ValueError): PkgPath('valid.1invalid')
    with pytest.raises(ValueError): PkgPath('1invalid.valid')

    # instantiation type check
    with pytest.raises(TypeError): PkgPath(123)
    with pytest.raises(TypeError): PkgPath([123])
    with pytest.raises(TypeError): PkgPath({'asdf'})  # not a sequence

    # pkg aliases are invalid everywhere
    with pytest.raises(ValueError): PkgPath(PkgPath.PKG_ALIAS_GROUP + '.asdf')
    with pytest.raises(ValueError): PkgPath('asdf.' + PkgPath.PKG_ALIAS_ROOT)

    # some keys are invalid
    with pytest.raises(ValueError): PkgPath(KEY_PACKAGE)
    with pytest.raises(ValueError): PkgPath(KEY_OPTIONS)
    with pytest.raises(ValueError): PkgPath(KEY_PACKAGE + '.asdf')
    with pytest.raises(ValueError): PkgPath('asdf.' + KEY_OPTIONS)

    # test reserved names & root values
    with pytest.raises(ValueError): PkgPath('global.asdf')
    PkgPath('')
    PkgPath([])

    with pytest.raises(ValueError): GroupPath('global.asdf')
    GroupPath('')
    GroupPath([])

    # check instantiation
    assert PkgPath('a.b.c') == 'a.b.c'
    assert PkgPath(('a', 'b', 'c')) == 'a.b.c'
    assert PkgPath(['a', 'b', 'c']) == 'a.b.c'
    assert PkgPath(PkgPath('a.b.c')) == 'a.b.c'

    # check equality
    assert PkgPath('a') == 'a'
    assert PkgPath('a.b.c') == 'a.b.c'
    assert PkgPath('a.b.c') == ('a', 'b', 'c')
    assert PkgPath('a.b.c') == ['a', 'b', 'c']
    assert PkgPath('a.b.c') == PkgPath('a.b.c')

    # check conversion
    assert PkgPath(GroupPath('a/b/c')) == 'a.b.c'
    assert PkgPath('a.b.c') == GroupPath('a/b/c')
    assert GroupPath(PkgPath('a.b.c')) == 'a/b/c'

    # test special packages
    with pytest.raises(ValueError): PkgPath(PkgPath.PKG_ALIAS_GROUP)
    with pytest.raises(ValueError): PkgPath(PkgPath.PKG_ALIAS_ROOT)


def test_config_group_paths():
    # add new root groups to option and test that the path changes
    option = ConfigOption({'asdf': 1})
    assert option.path == ''
    assert option.path == []
    with pytest.raises(AssertionError): option.group_path

    # check path and group paths
    ConfigGroup({'foo': option.root})
    assert option.path == 'foo'
    assert option.path == ['foo']
    assert option.group_path == ''
    assert option.group_path == []

    # check _group_ and _root_ aliases
    assert PkgPath.try_from_alias(PkgPath.PKG_ALIAS_GROUP, option) == ''
    assert PkgPath.try_from_alias(PkgPath.PKG_ALIAS_ROOT, option) == []
    ConfigGroup({'bar': option.root})
    assert PkgPath.try_from_alias(PkgPath.PKG_ALIAS_GROUP, option) == 'bar'
    assert PkgPath.try_from_alias(PkgPath.PKG_ALIAS_ROOT, option) == []
    ConfigGroup({'baz': option.root})
    assert PkgPath.try_from_alias(PkgPath.PKG_ALIAS_GROUP, option) == 'baz.bar'
    assert PkgPath.try_from_alias(PkgPath.PKG_ALIAS_ROOT, option) == []
    ConfigGroup({'buzz': option.root})
    assert PkgPath.try_from_alias(PkgPath.PKG_ALIAS_GROUP, option) == 'buzz.baz.bar'
    assert PkgPath.try_from_alias(PkgPath.PKG_ALIAS_ROOT, option) == []

    # check default alias
    assert PkgPath.try_from_alias(PkgPath.PKG_DEFAULT_ALIAS, option) == 'buzz.baz.bar'


@pytest.mark.parametrize("KeyType", [
    Key,
    Path,
    GroupKey,
    PkgKey,
    GroupPath,
    PkgPath
])
def test_keys_in_dicts(KeyType):
    assert {KeyType('foo'): 'bar'}['foo'] == 'bar'
    assert {'foo': 'bar'}[KeyType('foo')] == 'bar'

    assert {'foo', KeyType('foo')} == {'foo'}
    assert {'foo', KeyType('foo')} == {KeyType('foo')}

    assert {KeyType('foo'), 'foo'} == {'foo'}
    assert {KeyType('foo'), 'foo'} == {KeyType('foo')}

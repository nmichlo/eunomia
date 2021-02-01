import pytest
from eunomia._keys import PKG_ALIASES_ALL, KEYS_RESERVED_ALL, PKG_ALIAS_ROOT, PKG_ALIAS_GROUP, KEY_PACKAGE, KEY_OPTIONS
from eunomia._keys import assert_valid_single_key, is_valid_single_key
from eunomia._keys import assert_valid_value_package, is_valid_value_package, split_valid_value_package
from eunomia._keys import assert_valid_value_path, is_valid_value_path, split_valid_value_path


# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def test_eunomia_keys():
    assert_valid_single_key('asdf')
    assert_valid_single_key('_asdf')
    assert_valid_single_key('_asdf_')

    assert_valid_single_key(KEY_PACKAGE)
    assert_valid_single_key(KEY_OPTIONS)

    # package directive check -- TODO: maybe remove?
    with pytest.raises(ValueError): assert_valid_single_key(PKG_ALIAS_GROUP)
    with pytest.raises(ValueError): assert_valid_single_key(PKG_ALIAS_ROOT)

    # type check
    with pytest.raises(TypeError): assert_valid_single_key(123)
    with pytest.raises(TypeError): assert_valid_single_key(['asdf'])

    # invalid names check
    with pytest.raises(ValueError): assert_valid_single_key('asdf.fdsa')
    with pytest.raises(ValueError): assert_valid_single_key('1234')

    # keywords check
    with pytest.raises(ValueError): assert_valid_single_key('global')
    with pytest.raises(ValueError): assert_valid_single_key('is')

    # dict check -- TODO: maybe remove? This is very limiting.
    with pytest.raises(ValueError): assert_valid_single_key('items')
    with pytest.raises(ValueError): assert_valid_single_key('update')
    with pytest.raises(ValueError): assert_valid_single_key('values')
    with pytest.raises(ValueError): assert_valid_single_key('keys')

    assert is_valid_single_key('valid')
    assert not is_valid_single_key('1nvalid')


def test_eunomia_packages():
    assert_valid_value_package('asdf')
    assert_valid_value_package('asdf.fdsa')
    assert_valid_value_package(['asdf', 'fdsa'])
    assert_valid_value_package(('asdf', 'fdsa'))
    assert_valid_value_package('_asdf')
    assert_valid_value_package('_asdf_')

    # type check
    with pytest.raises(TypeError): assert_valid_value_package(123)
    with pytest.raises(TypeError): assert_valid_value_package([123])
    with pytest.raises(TypeError): assert_valid_value_package({'asdf'})

    # test special packages
    assert_valid_value_package(PKG_ALIAS_GROUP)
    assert_valid_value_package(PKG_ALIAS_ROOT)

    assert not is_valid_value_package(PKG_ALIAS_GROUP + '.asdf')
    assert not is_valid_value_package('asdf.' + PKG_ALIAS_ROOT)

    # keys are invalid
    assert not is_valid_value_package(KEY_PACKAGE)
    assert not is_valid_value_package(KEY_OPTIONS)
    assert not is_valid_value_package(KEY_PACKAGE + '.asdf')
    assert not is_valid_value_package('asdf.' + KEY_OPTIONS)

    # test reserved names
    with pytest.raises(ValueError): assert_valid_value_package('global.asdf')
    with pytest.raises(ValueError): assert_valid_value_package('')
    with pytest.raises(ValueError): assert_valid_value_package([])

    assert is_valid_value_package('valid')
    assert is_valid_value_package('valid.valid')

    assert not is_valid_value_package('1invalid')
    assert not is_valid_value_package('valid.1invalid')
    assert not is_valid_value_package('1invalid.valid')

    # test splitting
    assert split_valid_value_package('a') == ['a']
    assert split_valid_value_package('a.b.c') == ['a', 'b', 'c']
    assert split_valid_value_package(['a', 'b', 'c']) == ['a', 'b', 'c']


def test_eunomia_paths():
    """
    pretty much copy paste from above,
    but package directives are not allowed:
    PACKAGE_GROUP, PACKAGE_ROOT, etc.
    """

    assert_valid_value_path('asdf')
    assert_valid_value_path('asdf/fdsa')
    assert_valid_value_path(['asdf', 'fdsa'])
    assert_valid_value_path(('asdf', 'fdsa'))
    assert_valid_value_path('_asdf')
    assert_valid_value_path('_asdf_')

    # type check
    with pytest.raises(TypeError): assert_valid_value_path(123)
    with pytest.raises(TypeError): assert_valid_value_path([123])
    with pytest.raises(TypeError): assert_valid_value_path({'asdf'})

    # test special packages
    assert not is_valid_value_path(PKG_ALIAS_GROUP)
    assert not is_valid_value_path(PKG_ALIAS_ROOT)

    assert not is_valid_value_path(PKG_ALIAS_GROUP + '/asdf')
    assert not is_valid_value_path('asdf/' + PKG_ALIAS_ROOT)

    # keys are invalid
    assert not is_valid_value_path(KEY_PACKAGE)
    assert not is_valid_value_path(KEY_OPTIONS)
    assert not is_valid_value_path(KEY_PACKAGE + '/asdf')
    assert not is_valid_value_path('asdf/' + KEY_OPTIONS)

    # test reserved names
    with pytest.raises(ValueError): assert_valid_value_path('global/asdf')
    with pytest.raises(ValueError): assert_valid_value_path('')
    with pytest.raises(ValueError): assert_valid_value_path([])

    assert is_valid_value_path('valid')
    assert is_valid_value_path('valid/valid')

    assert not is_valid_value_path('1invalid')
    assert not is_valid_value_path('valid/1invalid')
    assert not is_valid_value_path('1invalid/valid')

    # test splitting
    assert split_valid_value_path('a') == ['a']
    assert split_valid_value_path('a/b/c') == ['a', 'b', 'c']
    assert split_valid_value_path(['a', 'b', 'c']) == ['a', 'b', 'c']


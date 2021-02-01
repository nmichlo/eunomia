import pytest
from eunomia._keys import ALL_PACKAGE_DIRECTIVES, ALL_RESERVED_KEYS, PACKAGE_ROOT, PACKAGE_GROUP, KEY_PACKAGE, KEY_OPTIONS
from eunomia._keys import assert_valid_eunomia_key, is_valid_eunomia_key
from eunomia._keys import assert_valid_eunomia_package, is_valid_eunomia_package, split_eunomia_package
from eunomia._keys import assert_valid_eunomia_path, is_valid_eunomia_path, split_eunomia_path


# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def test_eunomia_keys():
    assert_valid_eunomia_key('asdf')
    assert_valid_eunomia_key('_asdf')
    assert_valid_eunomia_key('_asdf_')

    assert_valid_eunomia_key(KEY_PACKAGE)
    assert_valid_eunomia_key(KEY_OPTIONS)

    # package directive check -- TODO: maybe remove?
    with pytest.raises(ValueError): assert_valid_eunomia_key(PACKAGE_GROUP)
    with pytest.raises(ValueError): assert_valid_eunomia_key(PACKAGE_ROOT)

    # type check
    with pytest.raises(TypeError): assert_valid_eunomia_key(123)
    with pytest.raises(TypeError): assert_valid_eunomia_key(['asdf'])

    # invalid names check
    with pytest.raises(ValueError): assert_valid_eunomia_key('asdf.fdsa')
    with pytest.raises(ValueError): assert_valid_eunomia_key('1234')

    # keywords check
    with pytest.raises(ValueError): assert_valid_eunomia_key('global')
    with pytest.raises(ValueError): assert_valid_eunomia_key('is')

    # dict check -- TODO: maybe remove? This is very limiting.
    with pytest.raises(ValueError): assert_valid_eunomia_key('items')
    with pytest.raises(ValueError): assert_valid_eunomia_key('update')
    with pytest.raises(ValueError): assert_valid_eunomia_key('values')
    with pytest.raises(ValueError): assert_valid_eunomia_key('keys')

    assert is_valid_eunomia_key('valid')
    assert not is_valid_eunomia_key('1nvalid')


def test_eunomia_packages():
    assert_valid_eunomia_package('asdf')
    assert_valid_eunomia_package('asdf.fdsa')
    assert_valid_eunomia_package(['asdf', 'fdsa'])
    assert_valid_eunomia_package(('asdf', 'fdsa'))
    assert_valid_eunomia_package('_asdf')
    assert_valid_eunomia_package('_asdf_')

    # type check
    with pytest.raises(TypeError): assert_valid_eunomia_package(123)
    with pytest.raises(TypeError): assert_valid_eunomia_package([123])
    with pytest.raises(TypeError): assert_valid_eunomia_package({'asdf'})

    # test special packages
    assert_valid_eunomia_package(PACKAGE_GROUP)
    assert_valid_eunomia_package(PACKAGE_ROOT)

    assert not is_valid_eunomia_package(PACKAGE_GROUP + '.asdf')
    assert not is_valid_eunomia_package('asdf.' + PACKAGE_ROOT)

    # keys are invalid
    assert not is_valid_eunomia_package(KEY_PACKAGE)
    assert not is_valid_eunomia_package(KEY_OPTIONS)
    assert not is_valid_eunomia_package(KEY_PACKAGE + '.asdf')
    assert not is_valid_eunomia_package('asdf.' + KEY_OPTIONS)

    # test reserved names
    with pytest.raises(ValueError): assert_valid_eunomia_package('global.asdf')
    with pytest.raises(ValueError): assert_valid_eunomia_package('')
    with pytest.raises(ValueError): assert_valid_eunomia_package([])

    assert is_valid_eunomia_package('valid')
    assert is_valid_eunomia_package('valid.valid')

    assert not is_valid_eunomia_package('1invalid')
    assert not is_valid_eunomia_package('valid.1invalid')
    assert not is_valid_eunomia_package('1invalid.valid')

    # test splitting
    assert split_eunomia_package('a') == ['a']
    assert split_eunomia_package('a.b.c') == ['a', 'b', 'c']
    assert split_eunomia_package(['a', 'b', 'c']) == ['a', 'b', 'c']


def test_eunomia_paths():
    """
    pretty much copy paste from above,
    but package directives are not allowed:
    PACKAGE_GROUP, PACKAGE_ROOT, etc.
    """

    assert_valid_eunomia_path('asdf')
    assert_valid_eunomia_path('asdf/fdsa')
    assert_valid_eunomia_path(['asdf', 'fdsa'])
    assert_valid_eunomia_path(('asdf', 'fdsa'))
    assert_valid_eunomia_path('_asdf')
    assert_valid_eunomia_path('_asdf_')

    # type check
    with pytest.raises(TypeError): assert_valid_eunomia_path(123)
    with pytest.raises(TypeError): assert_valid_eunomia_path([123])
    with pytest.raises(TypeError): assert_valid_eunomia_path({'asdf'})

    # test special packages
    assert not is_valid_eunomia_path(PACKAGE_GROUP)
    assert not is_valid_eunomia_path(PACKAGE_ROOT)

    assert not is_valid_eunomia_path(PACKAGE_GROUP + '/asdf')
    assert not is_valid_eunomia_path('asdf/' + PACKAGE_ROOT)

    # keys are invalid
    assert not is_valid_eunomia_path(KEY_PACKAGE)
    assert not is_valid_eunomia_path(KEY_OPTIONS)
    assert not is_valid_eunomia_path(KEY_PACKAGE + '/asdf')
    assert not is_valid_eunomia_path('asdf/' + KEY_OPTIONS)

    # test reserved names
    with pytest.raises(ValueError): assert_valid_eunomia_path('global/asdf')
    with pytest.raises(ValueError): assert_valid_eunomia_path('')
    with pytest.raises(ValueError): assert_valid_eunomia_path([])

    assert is_valid_eunomia_path('valid')
    assert is_valid_eunomia_path('valid/valid')

    assert not is_valid_eunomia_path('1invalid')
    assert not is_valid_eunomia_path('valid/1invalid')
    assert not is_valid_eunomia_path('1invalid/valid')

    # test splitting
    assert split_eunomia_path('a') == ['a']
    assert split_eunomia_path('a/b/c') == ['a', 'b', 'c']
    assert split_eunomia_path(['a', 'b', 'c']) == ['a', 'b', 'c']


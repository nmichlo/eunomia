import pytest
from schema import SchemaError
from eunomia.config import scheme as s


# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def _do_identifier_tests(schema, prefix=''):
    # check simple valid
    schema.validate(prefix + 'valid_id')
    with pytest.raises(SchemaError):  # TODO: fix , match="is_not_special_key"):
        schema.validate(prefix + '__type__')
    with pytest.raises(SchemaError):  # TODO: fix , match="is_not_reserved"):
        schema.validate(prefix + '__invalid_id__')
    schema.validate(prefix + '_okay_id_')
    with pytest.raises(SchemaError):  # TODO: fix , match="is_identifier"):
        schema.validate(prefix + '1234')
    with pytest.raises(SchemaError):  # TODO: fix , match="is_not_keyword"):
        schema.validate(prefix + 'with')
    with pytest.raises(SchemaError):  # TODO: fix , match="should be instance of"):
        schema.validate(1234)


def test_identifier():
    _do_identifier_tests(s.Identifier)


def test_pkg_path():
    # check - absolute
    assert s.PkgPath.validate('') == ''
    assert s.PkgPath.validate('valid1') == 'valid1'
    assert s.PkgPath.validate('valid1.valid2') == 'valid1.valid2'
    with pytest.raises(SchemaError): s.PkgPath.validate('valid1.')
    # check - relative
    assert s.PkgPath.validate('.') == '.'
    assert s.PkgPath.validate('.valid1') == '.valid1'
    assert s.PkgPath.validate('.valid1.valid2') == '.valid1.valid2'
    with pytest.raises(SchemaError): s.PkgPath.validate('.valid1.')

    # check splits - absolute
    assert s.split_pkg_path('') == ([], False)
    assert s.split_pkg_path('valid1') == (['valid1'], False)
    assert s.split_pkg_path('valid1.valid2') == (['valid1', 'valid2'], False)
    with pytest.raises(SchemaError): s.split_pkg_path('valid1.')
    # check splits - relative
    assert s.split_pkg_path('.') == ([], True)
    assert s.split_pkg_path('.valid1') == (['valid1'], True)
    assert s.split_pkg_path('.valid1.valid2') == (['valid1', 'valid2'], True)
    with pytest.raises(SchemaError): s.split_pkg_path('.valid1.')

    # check identifiers, should be same as above
    _do_identifier_tests(s.PkgPath)
    _do_identifier_tests(s.PkgPath, prefix='valid1.')
    _do_identifier_tests(s.PkgPath, prefix='_marker_.')
    with pytest.raises(SchemaError):  # TODO: fix , match='is_not_reserved'):
        _do_identifier_tests(s.PkgPath, prefix='__invalid1__.')

    # check group...
    with pytest.raises(SchemaError):  # TODO: fix , match='is_identifier'):
        s.PkgPath.validate('valid1/valid2/valid3')

    # check special keys
    s.PkgPath.validate('<root>')
    s.PkgPath.validate('<group>')
    # split special keys
    with pytest.raises(RuntimeError): s.split_pkg_path('<root>')
    with pytest.raises(RuntimeError): s.split_pkg_path('<group>')


def test_group_path():
    # check - relative
    assert s.ConfigPath.validate('') == ''
    assert s.ConfigPath.validate('valid1') == 'valid1'
    assert s.ConfigPath.validate('valid1/valid2') == 'valid1/valid2'
    with pytest.raises(SchemaError): s.ConfigPath.validate('valid1/')
    # check - absolute
    assert s.ConfigPath.validate('/') == '/'
    assert s.ConfigPath.validate('/valid1') == '/valid1'
    assert s.ConfigPath.validate('/valid1/valid2') == '/valid1/valid2'
    with pytest.raises(SchemaError): s.ConfigPath.validate('/valid1/')

    # check splits - relative
    assert s.split_config_path('') == ([], True)
    assert s.split_config_path('valid1') == (['valid1'], True)
    assert s.split_config_path('valid1/valid2') == (['valid1', 'valid2'], True)
    with pytest.raises(SchemaError): s.split_config_path('valid1/')
    # check splits - absolute
    assert s.split_config_path('/') == ([], False)
    assert s.split_config_path('/valid1') == (['valid1'], False)
    assert s.split_config_path('/valid1/valid2') == (['valid1', 'valid2'], False)
    with pytest.raises(SchemaError): s.split_config_path('/valid1/')

    # check identifiers, should be same as above
    _do_identifier_tests(s.ConfigPath)
    _do_identifier_tests(s.ConfigPath, prefix='valid1/')
    _do_identifier_tests(s.ConfigPath, prefix='_marker_/')
    with pytest.raises(SchemaError):  # TODO: fix , match='is_not_reserved'):
        _do_identifier_tests(s.ConfigPath, prefix='__invalid1__/')

    # check group...
    with pytest.raises(SchemaError):  # TODO: fix , match='is_identifier'):
        s.ConfigPath.validate('valid1.valid2.valid3')

    # check special keys
    with pytest.raises(SchemaError): s.ConfigPath.validate('<root>')
    with pytest.raises(SchemaError): s.ConfigPath.validate('<group>')
    # split special keys
    with pytest.raises(RuntimeError): s.split_pkg_path('<root>')
    with pytest.raises(RuntimeError): s.split_pkg_path('<group>')


def test_defaults():
    assert s.DefaultsValue.validate([]) == []

    # check self
    assert s.DefaultsValue.validate(['<self>']) == ['<self>']
    with pytest.raises(SchemaError):
        s.DefaultsValue.validate(['<self>s'])

    # check strings
    assert s.DefaultsValue.validate(['option1']) == ['option1']
    assert s.DefaultsValue.validate(['group/option1']) == ['group/option1']
    assert s.DefaultsValue.validate(['/option1']) == ['/option1']
    assert s.DefaultsValue.validate(['/group/option1']) == ['/group/option1']
    with pytest.raises(SchemaError):
        s.DefaultsValue.validate(['/1invalidgroup/option1'])

    # check dictionaries
    assert s.DefaultsValue.validate([{'group': 'option1'}]) == [{'group': 'option1'}]
    assert s.DefaultsValue.validate([{'/group': 'option1'}]) == [{'/group': 'option1'}]
    assert s.DefaultsValue.validate([{'group/subgroup': 'option1'}]) == [{'group/subgroup': 'option1'}]
    assert s.DefaultsValue.validate([{'/group/subgroup': 'option1'}]) == [{'/group/subgroup': 'option1'}]
    with pytest.raises(SchemaError):
        s.DefaultsValue.validate([{'/group/subgroup': '1invalidopt'}])
    with pytest.raises(SchemaError):
        s.DefaultsValue.validate([{'/1invalidgroup/subgroup': 'option1'}])

    # check lots
    assert s.DefaultsValue.validate([
        'group1/option1',
        'group2/option2',
        {'/group/subgroup': 'option1'},
        {'group/subgroup2': 'option2'},
        '<self>',
    ]) == [
        'group1/option1',
        'group2/option2',
        {'/group/subgroup': 'option1'},
        {'group/subgroup2': 'option2'},
        '<self>',
    ]


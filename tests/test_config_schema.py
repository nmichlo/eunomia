import pytest
from eunomia.config import keys as K
from eunomia.config import validate as V

# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def _do_identifier_tests(validator, prefix=''):
    # check simple valid
    validator(prefix + 'valid_id')
    with pytest.raises(ValueError):  # TODO: fix , match="is_not_special_key"):
        validator(prefix + '__type__')
    with pytest.raises(ValueError):  # TODO: fix , match="is_not_reserved"):
        validator(prefix + '__invalid_id__')
    validator(prefix + '_okay_id_')
    with pytest.raises(ValueError):  # TODO: fix , match="is_identifier"):
        validator(prefix + '1234')
    with pytest.raises(ValueError):  # TODO: fix , match="is_not_keyword"):
        validator(prefix + 'with')
    with pytest.raises(TypeError):  # TODO: fix , match="should be instance of"):
        validator(1234)


def test_identifier():
    _do_identifier_tests(V.validate_identifier)


def test_pkg_path():
    # check - absolute
    assert V.validate_package_path('') == ''
    assert V.validate_package_path('valid1') == 'valid1'
    assert V.validate_package_path('valid1.valid2') == 'valid1.valid2'
    with pytest.raises(ValueError): V.validate_package_path('valid1.')
    # check - relative
    assert V.validate_package_path('.') == '.'
    assert V.validate_package_path('.valid1') == '.valid1'
    assert V.validate_package_path('.valid1.valid2') == '.valid1.valid2'
    with pytest.raises(ValueError): V.validate_package_path('.valid1.')

    # check splits - absolute
    assert V.split_package_path('') == ([], False)
    assert V.split_package_path('valid1') == (['valid1'], False)
    assert V.split_package_path('valid1.valid2') == (['valid1', 'valid2'], False)
    with pytest.raises(ValueError): V.split_package_path('valid1.')
    # check splits - relative
    assert V.split_package_path('.') == ([], True)
    assert V.split_package_path('.valid1') == (['valid1'], True)
    assert V.split_package_path('.valid1.valid2') == (['valid1', 'valid2'], True)
    with pytest.raises(ValueError): V.split_package_path('.valid1.')

    # check identifiers, should be same as above
    _do_identifier_tests(V.validate_package_path)
    _do_identifier_tests(V.validate_package_path, prefix='valid1.')
    _do_identifier_tests(V.validate_package_path, prefix='_marker_.')
    with pytest.raises(ValueError):  # TODO: fix , match='is_not_reserved'):
        _do_identifier_tests(V.validate_package_path, prefix='__invalid1__.')

    # check group...
    with pytest.raises(ValueError):  # TODO: fix , match='is_identifier'):
        V.validate_package_path('valid1/valid2/valid3')

    # check special keys
    V.validate_package_path('<root>')
    V.validate_package_path('<group>')
    # split special keys
    with pytest.raises(RuntimeError): V.split_package_path('<root>')
    with pytest.raises(RuntimeError): V.split_package_path('<group>')


def test_group_path():
    # check - relative
    assert V.validate_config_path('') == ''
    assert V.validate_config_path('valid1') == 'valid1'
    assert V.validate_config_path('valid1/valid2') == 'valid1/valid2'
    with pytest.raises(ValueError): V.validate_config_path('valid1/')
    # check - absolute
    assert V.validate_config_path('/') == '/'
    assert V.validate_config_path('/valid1') == '/valid1'
    assert V.validate_config_path('/valid1/valid2') == '/valid1/valid2'
    with pytest.raises(ValueError): V.validate_config_path('/valid1/')

    # check splits - relative
    assert V.split_config_path('') == ([], True)
    assert V.split_config_path('valid1') == (['valid1'], True)
    assert V.split_config_path('valid1/valid2') == (['valid1', 'valid2'], True)
    with pytest.raises(ValueError): V.split_config_path('valid1/')
    # check splits - absolute
    assert V.split_config_path('/') == ([], False)
    assert V.split_config_path('/valid1') == (['valid1'], False)
    assert V.split_config_path('/valid1/valid2') == (['valid1', 'valid2'], False)
    with pytest.raises(ValueError): V.split_config_path('/valid1/')

    # check identifiers, should be same as above
    _do_identifier_tests(V.validate_config_path)
    _do_identifier_tests(V.validate_config_path, prefix='valid1/')
    _do_identifier_tests(V.validate_config_path, prefix='_marker_/')
    with pytest.raises(ValueError):  # TODO: fix , match='is_not_reserved'):
        _do_identifier_tests(V.validate_config_path, prefix='__invalid1__/')

    # check group...
    with pytest.raises(ValueError):  # TODO: fix , match='is_identifier'):
        V.validate_config_path('valid1.valid2.valid3')

    # check special keys
    with pytest.raises(ValueError): V.validate_config_path('<root>')
    with pytest.raises(ValueError): V.validate_config_path('<group>')
    # split special keys
    with pytest.raises(RuntimeError): V.split_package_path('<root>')
    with pytest.raises(RuntimeError): V.split_package_path('<group>')


def test_defaults():

    # check self
    assert V.split_defaults_item('<self>') == ('<self>', '<self>')
    with pytest.raises(ValueError):
        V.split_defaults_item(['<self>s'])

    # check strings
    assert V.split_defaults_item('option1') == ('', 'option1')
    assert V.split_defaults_item('/option1') == ('/', 'option1')
    assert V.split_defaults_item('group/option1') == ('group', 'option1')
    assert V.split_defaults_item('/group/option1') == ('/group', 'option1')
    with pytest.raises(ValueError):
        V.split_defaults_item('/1invalidgroup/option1')

    # check dictionaries
    assert V.split_defaults_item({'': 'option1'}) == ('', 'option1')
    assert V.split_defaults_item({'/': 'option1'}) == ('/', 'option1')
    assert V.split_defaults_item({'group': 'option1'}) == ('group', 'option1')
    assert V.split_defaults_item({'/group': 'option1'}) == ('/group', 'option1')
    with pytest.raises(ValueError):
        V.split_defaults_item({'/group/subgroup': '1invalidopt'})
    with pytest.raises(ValueError):
        V.split_defaults_item({'/1invalidgroup/subgroup': 'option1'})

    # check tuples
    assert V.split_defaults_item(('', 'option1')) == ('', 'option1')
    assert V.split_defaults_item(('/', 'option1')) == ('/', 'option1')
    assert V.split_defaults_item(('group', 'option1')) == ('group', 'option1')
    assert V.split_defaults_item(('/group', 'option1')) == ('/group', 'option1')

    assert V.split_defaults_item(['', 'option1']) == ('', 'option1')
    assert V.split_defaults_item(['/', 'option1']) == ('/', 'option1')
    assert V.split_defaults_item(['group', 'option1']) == ('group', 'option1')
    assert V.split_defaults_item(['/group', 'option1']) == ('/group', 'option1')


    # check lots
    assert V.split_defaults_list_items([]) == []
    assert V.split_defaults_list_items([
        'group1/option1',
        '/group2/option2',
        {'/group/subgroup': 'option1'},
        {'group/subgroup2': 'option2'},
        '<self>',
    ]) == [
        ('group1', 'option1'),
        ('/group2', 'option2'),
        ('/group/subgroup', 'option1'),
        ('group/subgroup2', 'option2'),
        ('<self>', '<self>'),
    ]


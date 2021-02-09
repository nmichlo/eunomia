import pytest
from schema import SchemaUnexpectedTypeError, SchemaError

from eunomia.config._schema import VerboseGroup, VerboseOption, CompactGroup, CompactOption, Identifier, PkgPath, \
    GroupPath


# ========================================================================= #
# Test YAML & Custom Tags                                                   #
# ========================================================================= #


def _do_identifier_tests(schema, prefix=''):
    # check simple valid
    schema.validate(prefix + 'valid_id')
    with pytest.raises(SchemaError, match="is_not_empty"):          schema.validate(prefix + '')
    with pytest.raises(SchemaError, match="is_not_special_key"):    schema.validate(prefix + '_name_')
    with pytest.raises(SchemaError, match="is_not_reserved"):       schema.validate(prefix + '_invalid_id_')
    with pytest.raises(SchemaError, match="is_identifier"):         schema.validate(prefix + '1234')
    with pytest.raises(SchemaError, match="is_not_keyword"):        schema.validate(prefix + 'with')
    with pytest.raises(SchemaError, match="should be instance of"): schema.validate(1234)


def test_identifier():
    _do_identifier_tests(Identifier)


def test_pkg_path():
    # check identifiers, should be same as above
    _do_identifier_tests(PkgPath)
    _do_identifier_tests(PkgPath, prefix='valid1.')
    with pytest.raises(SchemaError, match='is_not_reserved'): _do_identifier_tests(PkgPath, prefix='_invalid1_.')
    with pytest.raises(SchemaError, match='is_not_empty'): _do_identifier_tests(PkgPath, prefix='.')
    # check strings
    assert PkgPath.validate('valid1') == ['valid1']
    assert PkgPath.validate('valid1.valid2') == ['valid1', 'valid2']
    assert PkgPath.validate('valid1.valid2.valid3') == ['valid1', 'valid2', 'valid3']
    # check empty
    with pytest.raises(SchemaError, match="is_not_empty"): PkgPath.validate('')
    # check special keys
    PkgPath.validate('<root>')
    PkgPath.validate('<group>')
    # check group...
    with pytest.raises(SchemaError, match='is_identifier'):
        PkgPath.validate('valid1/valid2/valid3')


def test_group_path():
    # check identifiers, should be same as above
    _do_identifier_tests(GroupPath)
    _do_identifier_tests(GroupPath, prefix='valid1/')
    with pytest.raises(SchemaError, match='is_not_reserved'): _do_identifier_tests(GroupPath, prefix='_invalid1_.')
    with pytest.raises(SchemaError, match='is_not_empty'): _do_identifier_tests(GroupPath, prefix='.')
    # check strings
    assert GroupPath.validate('valid1') == ['valid1']
    assert GroupPath.validate('valid1/valid2') == ['valid1', 'valid2']
    assert GroupPath.validate('valid1/valid2/valid3') == ['valid1', 'valid2', 'valid3']
    # check empty
    with pytest.raises(SchemaError, match="is_not_empty"): GroupPath.validate('')
    # check special keys
    with pytest.raises(SchemaError, match='is_identifier'): GroupPath.validate('<root>')
    with pytest.raises(SchemaError, match='is_identifier'): GroupPath.validate('<group>')
    # check package...
    with pytest.raises(SchemaError, match='is_identifier'):
        GroupPath.validate('valid1.valid2.valid3')


def test_verbose_group():
    VerboseGroup.validate({'_type_': 'group', '_name_': 'valid_id'})

    # same tests as in identifier for _name_
    with pytest.raises(SchemaError, match="is_not_empty"):          VerboseGroup.validate({'_type_': 'group', '_name_': ''})
    with pytest.raises(SchemaError, match="is_not_special_key"):    VerboseGroup.validate({'_type_': 'group', '_name_': '_name_'})
    with pytest.raises(SchemaError, match="is_not_reserved"):       VerboseGroup.validate({'_type_': 'group', '_name_': '_invalid_id_'})
    with pytest.raises(SchemaError, match="is_identifier"):         VerboseGroup.validate({'_type_': 'group', '_name_': '1234'})
    with pytest.raises(SchemaError, match="is_not_keyword"):        VerboseGroup.validate({'_type_': 'group', '_name_': 'with'})
    with pytest.raises(SchemaError, match="should be instance of"): VerboseGroup.validate({'_type_': 'group', '_name_': 1234})



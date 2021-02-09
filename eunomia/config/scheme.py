import keyword as _keyword
from schema import Schema as _Schema
from schema import Optional as _Optional
from schema import Forbidden as _Forbidden
from schema import And as _And
from schema import Or as _Or
from schema import Use as _Use


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def _rename_fn(name, fn):
    """
    Wraps a function in an instance of a class with __call__ defined.
    The new class has its __repr__ set to the passed name.
    - Useful for schema error messages
    """
    class wrap:
        def __call__(self, *args, **kwargs):
            return fn(*args, **kwargs)
        def __repr__(self):
            return f'{name}'
    return wrap()


# ========================================================================= #
# Keys                                                                      #
# ========================================================================= #


# keys - all
KEY_TYPE = '_type_'
# keys - options
KEY_PKG = '_package_'
KEY_OPTS = '_defaults_'
KEY_DATA = '_data_'
# keys - groups
KEY_CHILDREN = '_children_'

# special types
TYPE_OPTION = 'option'
TYPE_GROUP  = 'group'
TYPE_COMPACT_OPTION = 'compact_option'
TYPE_COMPACT_GROUP  = 'compact_group'

# special packages
PKG_ROOT = '<root>'
PKG_GROUP = '<group>'

# defaults
DEFAULT_PKG = PKG_GROUP

# - - - - - - - - - - - - - #
# all values                #
# - - - - - - - - - - - - - #


ALL_KEYS = {KEY_TYPE, KEY_PKG, KEY_OPTS, KEY_DATA, KEY_CHILDREN}


# ========================================================================= #
# Helper Types                                                              #
# ========================================================================= #


Value = _Schema(None)
Value._schema = _Or(
    int,
    float,
    str,
    tuple([Value]),
    list([Value]),
    dict({Value: Value}),
)

Identifier = _Schema(_And(
    str,
    _rename_fn('is_not_empty',       lambda key: bool(key)),
    _rename_fn('is_identifier',      lambda key: str.isidentifier(key)),
    _rename_fn('is_not_keyword',     lambda key: not _keyword.iskeyword(key)),
    _rename_fn('is_not_special_key', lambda key: key not in ALL_KEYS),
    _rename_fn('is_not_reserved',    lambda key: not (key.startswith('_') and key.endswith('_'))),
), name='identifier')


def _make_path_list_schema(name, sep):
    return _Schema(_And(
        _Or(
            [str],
            _And(str, _Use(_rename_fn('can_split_pkg_path', lambda s: str.split(s, sep))))
        ),
        _Schema([Identifier])
    ), name=name)


PkgPath = _Schema(_Or(
    PKG_ROOT,
    PKG_GROUP,
    # sequentially convert and validate as a list of identifiers
    _make_path_list_schema('package_conv_path', sep='.')
), name='package_path')

GroupPath = _Schema((
    # sequentially convert and validate as a list of identifiers
    _make_path_list_schema('group_conv_path', sep='/')
), name='group_path')


# ========================================================================= #
# Sub Types                                                                 #
# ========================================================================= #


GroupNameValue  = _Schema(Identifier, name='group_name_value')
OptionNameValue = _Schema(Identifier, name='group_name_value')

PkgValue  = _Schema(_Or(PKG_ROOT, PKG_GROUP, PkgPath), name='pkg_value')
OptsValue = _Schema({_Optional(GroupPath): Identifier}, name='opts_value')
DataValue = _Schema({_Optional(Value): Value}, name='data_value')


# ========================================================================= #
# VERBOSE VERSIONS                                                          #
# - these versions are used internally                                      #
# ========================================================================= #


VerboseOption = _Schema({}, name='verbose_option')
VerboseOption.schema.update({
    _Optional(KEY_TYPE): TYPE_OPTION,
    _Optional(KEY_PKG, default=DEFAULT_PKG): PkgValue,
    _Optional(KEY_OPTS, default=dict):       OptsValue,
    _Optional(KEY_DATA, default=dict):       DataValue,
})

VerboseGroup = _Schema({}, name='verbose_group')
VerboseGroup.schema.update({
    _Optional(KEY_TYPE): TYPE_GROUP,
    _Optional(KEY_CHILDREN, default=list): {
        _Optional(GroupNameValue):  VerboseGroup,
        _Optional(OptionNameValue): VerboseOption,
    },
})


# ========================================================================= #
# COMPACT VERSIONS                                                          #
# - these versions you can store data directly on the objects with          #
#   your own keys. You do not need the _name_ tags                          #
# ========================================================================= #


# option
CompactOption = _Schema(None, name='compact_option')
CompactOption.schema.update({
    _Optional(KEY_TYPE):                     TYPE_COMPACT_OPTION,
    _Optional(KEY_PKG, default=DEFAULT_PKG): PkgValue,
    _Optional(KEY_OPTS, default=dict):       OptsValue,
    # _data_
    _Optional(OptionNameValue): Value,
})

# group
CompactGroup = _Schema(None, name='compact_group')
CompactGroup.schema.update({
        _Optional(KEY_TYPE): TYPE_COMPACT_GROUP,
        # children
        _Optional(GroupNameValue):  CompactGroup,
        _Optional(OptionNameValue): CompactOption,
})


# ========================================================================= #
# END                                                                       #
# ========================================================================= #


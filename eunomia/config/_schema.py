import keyword
from pprint import pprint
from schema import Schema, Optional, Forbidden, And, Or, Const, Use


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def rename_fn(name, fn):
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
KEY_NAME = '_name_'
# keys - options
KEY_PKG = '_package_'
KEY_OPTS = '_defaults_'
KEY_DATA = '_data_'
# keys - groups
KEY_SUBGROUPS = '_subgroups_'
KEY_SUBOPTIONS = '_suboptions_'

# special types
TYPE_OPTION = 'option'
TYPE_GROUP  = 'group'

# special packages
PKG_ROOT = '<root>'
PKG_GROUP = '<group>'

# defaults
DEFAULT_PKG = PKG_GROUP

# all values
ALL_KEYS = {KEY_TYPE, KEY_NAME, KEY_PKG, KEY_OPTS, KEY_DATA, KEY_SUBGROUPS, KEY_SUBOPTIONS}
ALL_VALS = {TYPE_OPTION, TYPE_GROUP, PKG_ROOT, PKG_GROUP}

ALL_GROUP_KEYS = {KEY_TYPE, KEY_NAME, KEY_SUBGROUPS, KEY_SUBOPTIONS}
ALL_OPTION_KEYS = {KEY_TYPE, KEY_NAME, KEY_PKG, KEY_OPTS, KEY_DATA}


# ========================================================================= #
# Helper Types                                                              #
# ========================================================================= #


Value = Schema(None)
Value._schema = Or(
    int,
    float,
    str,
    tuple([Value]),
    list([Value]),
    dict({Value: Value}),
)

Identifier = Schema(And(
    str,
    rename_fn('is_not_empty',       lambda key: bool(key)),
    rename_fn('is_identifier',      lambda key: str.isidentifier(key)),
    rename_fn('is_not_keyword',     lambda key: not keyword.iskeyword(key)),
    rename_fn('is_not_special_key', lambda key: key not in ALL_KEYS),
    rename_fn('is_not_reserved',    lambda key: not (key.startswith('_') and key.endswith('_'))),
), name='identifier')


def _make_path_list_schema(name, sep):
    return Schema(And(
        Or(
            [str],
            And(str, Use(rename_fn('can_split_pkg_path', lambda s: str.split(s, sep))))
        ),
        Schema([Identifier])
    ), name=name)


PkgPath = Schema(Or(
    PKG_ROOT,
    PKG_GROUP,
    # sequentially convert and validate as a list of identifiers
    _make_path_list_schema('package_conv_path', sep='.')
), name='package_path')

GroupPath = Schema((
    # sequentially convert and validate as a list of identifiers
    _make_path_list_schema('group_conv_path', sep='/')
), name='group_path')


# ========================================================================= #
# Sub Types                                                                 #
# ========================================================================= #


GroupNameValue  = Schema(Identifier,                  name='group_name_value')
OptionNameValue = Schema(Identifier,                  name='group_name_value')

PkgValue  = Schema(Or(PKG_ROOT, PKG_GROUP, PkgPath),  name='pkg_value')
OptsValue = Schema({Optional(GroupPath): Identifier}, name='opts_value')
DataValue = Schema({Optional(Value): Value},          name='data_value')


# ========================================================================= #
# Options                                                                   #
# ========================================================================= #


VerboseOption = Schema({}, name='verbose_option')
VerboseOption.schema.update({
    KEY_NAME: OptionNameValue,
    Optional(KEY_TYPE): TYPE_OPTION,
    Optional(KEY_PKG,  default=DEFAULT_PKG): PkgValue,
    Optional(KEY_OPTS, default=dict):        OptsValue,
    Optional(KEY_DATA, default=dict):        DataValue,
    # not allowed keys from other groups
    Forbidden(Or(*(ALL_KEYS - ALL_OPTION_KEYS))): object,
})


# ========================================================================= #
# Groups                                                                    #
# ========================================================================= #


VerboseGroup = Schema({}, name='verbose_group')
VerboseGroup.schema.update({
    KEY_NAME: GroupNameValue,
    Optional(KEY_TYPE): TYPE_GROUP,
    Optional(KEY_SUBGROUPS,  default=list): [VerboseGroup],
    Optional(KEY_SUBOPTIONS, default=list): [VerboseOption],
    # not allowed keys from other groups
    Forbidden(Or(*(ALL_KEYS - ALL_GROUP_KEYS))): object,
})


# ========================================================================= #
# COMPACT VERSIONS                                                          #
# - these versions you can store data directly on the objects with          #
#   your own keys. You do not need the _name_ tags                          #
# ========================================================================= #


def _convert_compact_option_to_verbose_option(option):
    pprint(option)
    return option

def _convert_compact_group_to_verbose_group(group):
    pprint(group)
    return group


# extra - special types
TYPE_COMPACT_OPTION = 'compact_option'
TYPE_COMPACT_GROUP  = 'compact_group'

# update - all keys
ALL_KEYS.update({TYPE_COMPACT_OPTION, TYPE_COMPACT_GROUP})
ALL_COMPACT_GROUP_KEYS = {KEY_TYPE}
ALL_COMPACT_OPTION_KEYS = {KEY_TYPE, KEY_PKG, KEY_OPTS}

# option
CompactOption = Schema(None, name='compact_option')
CompactOption._schema = And(
    {
        Optional(KEY_TYPE):                      TYPE_COMPACT_OPTION,
        Optional(KEY_PKG,  default=DEFAULT_PKG): PkgValue,
        Optional(KEY_OPTS, default=dict):        OptsValue,
        # _data_
        Optional(OptionNameValue): Value,
        # not allowed keys from other groups
        Forbidden(Or(*(ALL_KEYS - ALL_COMPACT_OPTION_KEYS))): object,
    },
    Use(_convert_compact_option_to_verbose_option),
    VerboseOption,
)

# group
CompactGroup = Schema(None, name='compact_group')
CompactGroup._schema = And(
    {
        Optional(KEY_TYPE): TYPE_COMPACT_GROUP,
        # _subgroups_ & _suboptions_
        Optional(GroupNameValue): CompactGroup,
        Optional(OptionNameValue): CompactOption,
        # not allowed keys from other groups
        Forbidden(Or(*(ALL_KEYS - ALL_COMPACT_GROUP_KEYS))): object,
    },
    Use(_convert_compact_group_to_verbose_group),
    VerboseGroup,
)


# ========================================================================= #
# END                                                                       #
# ========================================================================= #


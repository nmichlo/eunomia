import keyword as _keyword
from schema import Schema as _Schema
from schema import Optional as _Optional
from schema import And as _And
from schema import Or as _Or
from schema import Use as _Use
from schema import Const as _Const
from schema import Regex as _Regex


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def _rename_fn(name, fn, debug=False):
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
    if debug:
        return _debug_fn(wrap())
    return wrap()


def _debug_fn(fn):
    def wrap(*args, **kwargs):
        print(f'{repr(fn)} called with: args={args}, kwargs={kwargs}')
        result = fn(*args, **kwargs)
        print(f'- result: {result}')
        return result
    return wrap


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
# keys - values
KEY_NODE   = '_node_'    # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED
KEY_TARGET = '_target_'  # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED
KEY_ARGS   = '_args_'    # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED
KEY_KWARGS = '_kwargs_'  # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED
KEY_VALUE  = '_value_'   # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED

# special types
TYPE_OPTION = 'option'
TYPE_GROUP  = 'group'
TYPE_COMPACT_OPTION = 'compact_option'
TYPE_COMPACT_GROUP  = 'compact_group'

# special packages
PKG_ROOT = '<root>'
PKG_GROUP = '<group>'

# special options
OPT_SELF = '<self>'

# defaults
DEFAULT_PKG = PKG_GROUP

# - - - - - - - - - - - - - #
# all values                #
# - - - - - - - - - - - - - #


ALL_KEYS = {
    KEY_TYPE, KEY_PKG, KEY_OPTS, KEY_DATA, KEY_CHILDREN,
    # TODO: THESE ARE NOT IMPLEMENTED, JUST RESERVED
    KEY_NODE, KEY_TARGET, KEY_ARGS, KEY_KWARGS, KEY_VALUE
}


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

IdentifierList = _Schema([Identifier], name='identifier_list')


def _split_path(path: str, sep: str):
    # check and remove prefix
    is_prefixed = False
    if path.startswith(sep):
        is_prefixed, path = True, path[len(sep):]
    # split path
    if path:
        split = str.split(path, sep)
    else:
        split = []
    # check identifiers
    return IdentifierList.validate(split), is_prefixed


def split_pkg_path(path: str):
    if path in {PKG_GROUP, PKG_ROOT}:
        raise RuntimeError('special package keys should be handled separately')
    keys, is_relative = _split_path(path, '.')
    return keys, is_relative


def split_group_path(path: str):
    keys, is_not_relative = _split_path(path, '/')
    return keys, not is_not_relative


PkgPath = _Schema(_Or(
    PKG_ROOT,
    PKG_GROUP,
    # sequentially convert and validate as a list of identifiers
    _And(str, _Const(split_pkg_path))
), name='package_path')

GroupPath = _Schema((
    # sequentially convert and validate as a list of identifiers
    _And(str, _Const(split_group_path))
), name='group_path')


# ========================================================================= #
# Sub Types                                                                 #
# ========================================================================= #


NameKey  = _Schema(Identifier, name='name_key')

PkgValue  = _Schema(_Or(PKG_ROOT, PKG_GROUP, PkgPath), name=KEY_PKG)
DataValue = _Schema({_Optional(Value): Value}, name=KEY_DATA)
OptsValue = _Schema({
    _Optional(OPT_SELF, default=None): None,
    _Optional(GroupPath): Identifier
}, name=KEY_OPTS)


# ========================================================================= #
# VERBOSE VERSIONS                                                          #
# - these versions are used internally                                      #
# ========================================================================= #


VerboseOption = _Schema({}, name='verbose_option')
VerboseOption.schema.update({
    _Optional(KEY_TYPE, default=TYPE_OPTION): TYPE_OPTION,
    _Optional(KEY_PKG, default=DEFAULT_PKG): PkgValue,
    _Optional(KEY_OPTS, default=dict):       OptsValue,
    _Optional(KEY_DATA, default=dict):       DataValue,
})

VerboseGroup = _Schema({}, name='verbose_group')
VerboseGroup.schema.update({
    _Optional(KEY_TYPE, default=TYPE_GROUP): TYPE_GROUP,
    _Optional(KEY_CHILDREN, default=list): {
        _Optional(NameKey): _Or(VerboseOption, VerboseGroup),
    },
})


# ========================================================================= #
# COMPACT VERSIONS                                                          #
# - these versions you can store data directly on the objects with          #
#   your own keys. You do not need the _name_ tags                          #
# ========================================================================= #


# option
CompactOption = _Schema({}, name='compact_option')
CompactOption.schema.update({
    _Optional(KEY_TYPE, default=TYPE_COMPACT_OPTION): TYPE_COMPACT_OPTION,
    _Optional(KEY_PKG, default=DEFAULT_PKG): PkgValue,
    _Optional(KEY_OPTS, default=dict):       OptsValue,
    # _data_
    _Optional(NameKey): Value,
})

# group
CompactGroup = _Schema({}, name='compact_group')
CompactGroup.schema.update({
        _Optional(KEY_TYPE, default=TYPE_COMPACT_GROUP): TYPE_COMPACT_GROUP,
        # children
        _Optional(NameKey): _Or(CompactOption, CompactGroup),
})


# ========================================================================= #
# END                                                                       #
# ========================================================================= #


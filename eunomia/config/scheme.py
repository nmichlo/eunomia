import keyword as _keyword
from schema import Schema as _Schema
from schema import Optional as _Optional
from schema import And as _And
from schema import Or as _Or
from schema import Use as _Use
from schema import Const as _Const
from schema import Regex as _Regex
from schema import SchemaError as _SchemaError


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
KEY_TYPE = '__type__'
# keys - options
KEY_PKG = '__package__'
KEY_MERGE = '__include__'
KEY_DATA = '__data__'
# keys - groups
KEY_CHILDREN = '__children__'

# marker keys - these are not reserved
MARKER_KEY_TARGET = '_target_'  # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED
MARKER_KEY_ARGS   = '_args_'    # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED
MARKER_KEY_KWARGS = '_kwargs_'  # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED
MARKER_KEY_VALUE  = '_value_'   # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED

# special types
TYPE_OPTION = 'option'
TYPE_GROUP  = 'group'
TYPE_NODE  = 'node'             # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED

# special packages
PKG_ROOT = '<root>'
PKG_GROUP = '<group>'

# special options
OPT_SELF = '<self>'

# include
DEFAULT_PKG = PKG_GROUP

# - - - - - - - - - - - - - #
# all values                #
# - - - - - - - - - - - - - #

# these keys are allowed as values anywhere and are not reserved
_MARKER_KEYS = {
    MARKER_KEY_TARGET,
    MARKER_KEY_ARGS,
    MARKER_KEY_KWARGS,
    MARKER_KEY_VALUE
}

_RESERVED_GROUP_KEYS = {
    KEY_TYPE, KEY_PKG, KEY_MERGE, KEY_DATA,
}

_RESERVED_OPTION_KEYS = {
    KEY_TYPE, KEY_CHILDREN,
}

# TODO: not yet implemented
_RESERVED_NODE_KEYS = {
    KEY_TYPE, KEY_DATA,
}

# these keys are not allowed in normal data
RESERVED_KEYS = {
    *_RESERVED_GROUP_KEYS,
    *_RESERVED_OPTION_KEYS,
    *_RESERVED_NODE_KEYS,
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
    _rename_fn('is_not_special_key', lambda key: key not in RESERVED_KEYS),
    _rename_fn('is_not_reserved',    lambda key: not (key.startswith('__') and key.endswith('__'))),  # we allow one underscore on each side for markers
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
MergersValue = _Schema({
    _Optional(OPT_SELF, default=None): None,
    _Optional(GroupPath): Identifier
}, name=KEY_MERGE)


# ========================================================================= #
# VERBOSE VERSIONS                                                          #
# - these versions are used internally                                      #
# ========================================================================= #


VerboseOption = _Schema({}, name='verbose_option')
VerboseOption.schema.update({
    _Optional(KEY_TYPE, default=TYPE_OPTION): TYPE_OPTION,
    _Optional(KEY_PKG, default=DEFAULT_PKG): PkgValue,
    _Optional(KEY_MERGE, default=dict):      MergersValue,
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
# END                                                                       #
# ========================================================================= #


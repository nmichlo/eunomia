import keyword as _keyword

# ========================================================================= #
# Keys                                                                      #
# ========================================================================= #


# keys - all

KEY_TYPE = '__type__'
# keys - options
KEY_PKG = '__package__'
KEY_DEFAULTS = '__defaults__'
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
TYPE_NODE   = 'node'            # TODO: THIS IS NOT IMPLEMENTED, JUST RESERVED

# special packages
PKG_ROOT = '<root>'
PKG_GROUP = '<group>'

# special options
OPT_SELF = '<self>'

# default
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

RESERVED_OPTION_KEYS = {
    KEY_TYPE, KEY_PKG, KEY_DEFAULTS, KEY_DATA,
}

RESERVED_GROUP_KEYS = {
    KEY_TYPE, KEY_CHILDREN,
}

# TODO: not yet implemented
_RESERVED_NODE_KEYS = {
    KEY_TYPE, KEY_DATA,
}

# these keys are not allowed in normal data
RESERVED_KEYS = {
    *RESERVED_GROUP_KEYS,
    *RESERVED_OPTION_KEYS,
    *_RESERVED_NODE_KEYS,
}


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

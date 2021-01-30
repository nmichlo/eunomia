

# ========================================================================= #
# Loaders                                                                   #
# ========================================================================= #


def recursive_update_dict(left, right, stack=None):
    if stack is None:
        stack = []
    # b takes priority
    for k, v in right.items():
        if k in left:
            if isinstance(left[k], dict) or isinstance(v, dict):
                new_stack = stack + [k]
                if not (isinstance(left[k], dict) and isinstance(v, dict)):
                    raise TypeError(f'Recursive update cannot merge keys with a different type if one is a dictionary. {".".join(new_stack)}')
                else:
                    recursive_update_dict(left[k], v, stack=new_stack)
                    continue
        left[k] = v

# ========================================================================= #
# Printing                                                                  #
# ========================================================================= #


def fmt_pntr(line, i, message, arrow='^--- '):
    return f'{line}\n{" " * i}{arrow}{message}'


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

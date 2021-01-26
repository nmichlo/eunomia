import os


# ========================================================================= #
# Path Util                                                                 #
# ========================================================================= #


EXT = '.yaml'


def remove_extension(path):
    base, ext = os.path.splitext(path)
    if ext == EXT:
        return base
    return path


def add_extension(path):
    base, ext = os.path.splitext(path)
    if ext != EXT:
        return f'{path}{EXT}'
    return path


def split_dirs_base(path):
    base, conf = os.path.split(path)
    base = base.rstrip('/')
    conf = remove_extension(conf)
    return base, conf


def split_elems(path):
    return remove_extension(path).strip('/').split('/')


def split_subgroups_config(path):
    subgroups = split_elems(path)
    subgroups, subconfig = subgroups[:-1], subgroups[-1]
    return subgroups, subconfig


def recursive_get(dct, keys):
    for key in keys:
        dct = dct[key]
    return dct

# ========================================================================= #
# Loaders                                                                   #
# ========================================================================= #


def recursive_update(left, right, stack=None):
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
                    recursive_update(left[k], v, stack=new_stack)
                    continue
        left[k] = v

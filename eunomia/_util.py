import os


# ========================================================================= #
# Path Util                                                                 #
# ========================================================================= #


class conf_paths:

    EXT = '.yaml'

    @staticmethod
    def remove_extension(path):
        base, ext = os.path.splitext(path)
        if ext == conf_paths.EXT:
            return base
        return path

    @staticmethod
    def add_extension(path):
        base, ext = os.path.splitext(path)
        if ext != conf_paths.EXT:
            return f'{path}{conf_paths.EXT}'
        return path

    @staticmethod
    def split_dirs_base(path):
        base, conf = os.path.split(path)
        base = base.rstrip('/')
        conf = conf_paths.remove_extension(conf)
        return base, conf

    @staticmethod
    def split_elems(path):
        return conf_paths.remove_extension(path).strip('/').split('/')

    @staticmethod
    def split_subgroups_config(path):
        subgroups = conf_paths.split_elems(path)
        subgroups, subconfig = subgroups[:-1], subgroups[-1]
        return subgroups, subconfig

    @staticmethod
    def recursive_get(dct, keys):
        for key in keys:
            dct = dct[key]
        return dct


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

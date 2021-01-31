
# ========================================================================= #
# Group                                                                     #
# ========================================================================= #
import os


class Group(object):

    def __init__(self):
        super().__init__()
        self._groups = {}
        self._options = {}

    def _check_uninserted(self, name):
        # TODO: maybe relax limitation that groups
        #       and options should have different names?
        assert str.isidentifier(name)
        assert name not in self._groups
        assert name not in self._options

    def new_subgroup(self, name) -> 'Group':
        self.__check_uninserted(name)
        self._groups[name] = Group()
        return self._groups[name]

    def add_option(self, name, conf) -> 'Group':
        self.__check_uninserted(name)
        self._options[name] = conf
        return self

    def get_subgroup(self, name) -> 'Group':
        return self._groups[name]

    def get_option(self, name) -> dict:
        return self._options[name]

    def __getitem__(self, name):
        if name in self._options:
            return self._options[name]
        if name in self._groups:
            return self._groups[name]
        raise KeyError

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:
            return self.__getattribute__(name)


# ========================================================================= #
# Option                                                                    #
# ========================================================================= #


class Option(object):

    KEY_OPTIONS = '_options_'  # default is {}
    KEY_PACKAGE = '_package_'  # default is _group_

    PACKAGE_GROUP = '_group_'
    PACKAGE_GLOBAL = '_global_'

    def __init__(self, dct: dict, path: list[str]):
        self.path = path
        # extract various components from the config
        self.defaults = self._config_pop_options(dct)
        self.package = self._config_pop_package(dct)
        self.dct = dct

    def _error_msg(self, message: str):
        raise os.path.join(self.path) + message


    def _config_pop_options(self, data: dict) -> dict:
        defaults = data.pop(Option.KEY_OPTIONS, {})
        assert isinstance(defaults, dict), f'Config: {self.path=} ERROR: defaults must be a mapping!'
        # check that the chosen options are valid!
        for k, v in defaults.items():
            if not isinstance(k, str): raise TypeError(self._error_msg('keys in chosen options must be strings.'))
            if not isinstance(v, str): raise TypeError(self._error_msg('values in chosen options must be strings.'))
            if not str.isidentifier(k): raise ValueError('keys must be valid identifiers.')

        return defaults

    def _config_pop_package(self, data: dict) -> str:
        package = data.pop(Option.KEY_OPTIONS, Option.PACKAGE_GROUP)
        assert isinstance(package, str), f'Config: {self.path=} ERROR: package must be a string!'
        return package



class ObjTransformer(object):

    def __init__(self, visit_keys=True):
        self.visit_keys = visit_keys

    def visit(self, value):
        attr = f'_visit_{type(value).__name__}'
        func = getattr(self, attr)
        return func(value)

    def __getattr__(self, name):
        return self.__default__

    def __default__(self, value):
        return value

    def _visit_set(self, value):
        return set(self.visit(v) for v in value)

    def _visit_list(self, value):
        return list(self.visit(v) for v in value)

    def _visit_tuple(self, value):
        return tuple(self.visit(v) for v in value)

    def _visit_dict(self, value):
        if self.visit_keys:
            return dict((self.visit(k), self.visit(v)) for k, v in value.items())
        return dict((k, self.visit(v)) for k, v in value.items())


def _is_valid_eunomia_key(key):
    if not isinstance(key, str):
        raise TypeError(f'Eunomia keys must be strings: {repr(key)}')
    if not str.isidentifier(key):
        raise ValueError(f'Keys must be valid identifiers: {repr(key)}')
    return key



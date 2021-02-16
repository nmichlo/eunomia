from typing import Union

from eunomia.config import Group as Group, Option


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class Backend(object):

    """
    A backend is an instance of various settings needed to load
    a group or option from some value.
    """

    @classmethod
    @property
    def GROUP_TYPE(self):
        raise NotImplementedError

    @classmethod
    @property
    def OPTION_TYPE(self):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Load                                                                  #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def load_group(self, value: GROUP_TYPE):
        if not isinstance(value, self.GROUP_TYPE):
            raise TypeError(f'group value must be of type: {self.GROUP_TYPE}')
        group = self._load_group(value)
        assert isinstance(group, Group), f'loaded group must be a: {Group}'
        return group

    def load_option(self, value: OPTION_TYPE):
        if not isinstance(value, self.OPTION_TYPE):
            raise TypeError(f'option value must be of type: {self.OPTION_TYPE}')
        option = self._load_option(value)
        assert isinstance(option, Option), f'loaded option must be a: {Option}'
        return option

    def _load_group(self, value: GROUP_TYPE) -> Group:
        raise NotImplementedError

    def _load_option(self, value: OPTION_TYPE) -> Option:
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Dump                                                                  #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def dump(self, config: Union[Group, Option]):
        if isinstance(config, Group):
            return self.dump_group(config)
        elif isinstance(config, Option):
            return self.dump_option(config)
        else:
            raise TypeError(f'unsupported config type: {type(config)}')

    def dump_group(self, group: Group):
        if not isinstance(group, Group):
            raise TypeError(f'group must be a: {Group}')
        value = self._dump_group(group)
        assert isinstance(value, self.GROUP_TYPE), f'dumped group value must be of type: {self.GROUP_TYPE}'
        return value

    def dump_option(self, option: Option):
        if not isinstance(option, Option):
            raise TypeError(f'option must be a: {Option}')
        value = self._dump_option(option)
        assert isinstance(value, self.OPTION_TYPE), f'dumped option value must be of type: {self.OPTION_TYPE}'
        return value

    def _dump_group(self, group: Group):
        raise NotImplementedError

    def _dump_option(self, option: Option):
        raise NotImplementedError


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

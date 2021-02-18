

# ========================================================================= #
# SimpleAttrDict                                                            #
# ========================================================================= #


class AttrDict(dict):
    """
    Nested Attribute Dictionary

    A class to convert a nested Dictionary into an object with key-values
    accessible using attribute notation (AttrDict.attribute) in addition to
    key notation (Dict["key"]). This class recursively sets Dicts to objects,
    allowing you to recurse into nested dicts (like: AttrDict.attr.attr)

    https://stackoverflow.com/a/48806603/9852408
    """

    def __init__(self, mapping=None):
        super(AttrDict, self).__init__()
        # add all values to dictionary
        if mapping is not None:
            for key, value in mapping.items():
                self.__setitem__(key, value)

    def __setitem__(self, key, value):
        # recursively convert dicts to attrdicts TODO: convert sub-lists and dicts too!
        if isinstance(value, dict):
            value = AttrDict(value)
        # set item like usual
        super(AttrDict, self).__setitem__(key, value)
        # for code completion in editors
        self.__dict__[key] = value

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError

    __setattr__ = __setitem__

    # def __setattr__(self, key, value):
    #     # allow double underscores to be assigned to the class itself
    #     if str.startswith(key, f'_{self.__class__.__name__}__'):
    #         super().__setattr__(key, value)
    #     else:
    #         return self.__setitem__(key, value)



# ========================================================================= #
# End                                                                       #
# ========================================================================= #


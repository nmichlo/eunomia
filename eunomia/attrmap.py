import keyword


# ========================================================================= #
# SimpleAttrDict                                                            #
# ========================================================================= #


class SimpleAttrDict(dict):
    """
    Nested Attribute Dictionary

    A class to convert a nested Dictionary into an object with key-values
    accessible using attribute notation (AttrDict.attribute) in addition to
    key notation (Dict["key"]). This class recursively sets Dicts to objects,
    allowing you to recurse into nested dicts (like: AttrDict.attr.attr)

    https://stackoverflow.com/a/48806603/9852408
    """

    def __init__(self, mapping=None):
        super(SimpleAttrDict, self).__init__()
        if mapping is not None:
            for key, value in mapping.items():
                self.__setitem__(key, value)

    def __setitem__(self, key, value):
        # TODO: convert sub-lists and dicts too!
        if isinstance(value, dict):
            value = SimpleAttrDict(value)
        super(SimpleAttrDict, self).__setitem__(key, value)
        self.__dict__[key] = value  # for code completion in editors

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    __setattr__ = __setitem__


# # ========================================================================= #
# # AttrDict                                                                  #
# # ========================================================================= #
#
#
# class AttrMap(object):
#     """
#     Nested Attribute Dictionary
#
#     A class that acts like a dictionary but without
#     all the frills and additional functions.
#
#     Based on:
#     https://stackoverflow.com/a/48806603/9852408
#     """
#
#     __INVALID_ITEM_NAMES = {}
#
#     def __init__(self, mapping=None):
#         # initialise this dict
#         super(AttrMap, self).__init__()
#         # add all keys and values to dict
#         if mapping:
#             attrhelp.update(self, mapping)
#
#     def __len__(self): return self.__dict__.__len__()
#     def __iter__(self): return self.__dict__.__iter__()
#     def __str__(self): return self.__dict__.__str__()
#     def __repr__(self): return self.__dict__.__repr__()
#
#     def __getitem__(self, key):
#         return self.__dict__.__getitem__(key)
#
#     def __setitem__(self, key, value):
#         if not str.isidentifier(key):
#             raise KeyError(f'{key=} must be a valid python identifier.')
#         if key in AttrMap.__INVALID_ITEM_NAMES:
#             raise KeyError(f'{key=} name is not allowed.')
#         # recursively merge dictionaries
#         value = attrhelp.recursive_to_attrdict(value)
#         # set the key in the dictionary
#         self.__dict__[key] = value
#
#     def __getattr__(self, item):
#         try:
#             return self.__getitem__(item)
#         except KeyError:
#             raise AttributeError(item)
#
#     __setattr__ = __setitem__
#
#     # custom dict implementations
#     # other names are reserved but not used
#
#     def __keys(self):   return self.__dict__.keys()
#     def __values(self): return self.__dict__.values()
#     def __items(self):  return self.__dict__.items()
#
#     def __update(self, mapping):
#         for k, v in attrhelp.items(mapping):
#             self.__setitem__(k, v)
#
#
# # ========================================================================= #
# # Names Not Allowed                                                         #
# # ========================================================================= #
#
#
# # update the invalid names
# AttrMap.__INVALID_ITEM_NAMES = {
#     # python reserved words, eg. def, class, global, etc
#     *keyword.kwlist,
#     # reserve dictionary keys for future use
#     *[k if k.startswith('__') else f'_{k}_' for k in dir(dict)],                      # eg. _get_
#     *[k if k.startswith('__') else f'__{k}' for k in dir(dict)],                      # eg. __get
#     *[k if k.startswith('__') else f'_{AttrMap.__name__}__{k}' for k in dir(dict)],  # eg. _AttrMap__get_
#     # values obtained from this class
#     *dir(AttrMap)
# }
#
#
# # ========================================================================= #
# # Helper                                                                    #
# # ========================================================================= #
#
#
# def _recursive_convert(value, dict_type):
#     """
#     NOTE: This function works in conjunction with the constructor above.
#     """
#     if isinstance(value, (dict, AttrMap)):
#         if issubclass(dict_type, AttrMap):
#             # AttrMap calls _recursive_convert internally
#             return dict_type(value)
#         else:
#             return {k: _recursive_convert(v, dict_type=dict_type) for k, v in attrhelp.items(value)}
#     elif isinstance(value, list):
#         return list(_recursive_convert(v, dict_type=dict_type) for v in value)
#     elif isinstance(value, tuple):
#         return tuple(_recursive_convert(v, dict_type=dict_type) for v in value)
#     elif isinstance(value, set):
#         return set(_recursive_convert(v, dict_type=dict_type) for v in value)
#     else:
#         return value
#
#
# def _recursive_update_map(left, right, stack):
#     # b takes priority
#     for k, v in attrhelp.items(right):
#         if k in left:
#             if isinstance(left[k], dict) or isinstance(v, dict):
#                 new_stack = stack + [k]
#                 if not (isinstance(left[k], dict) and isinstance(v, dict)):
#                     raise TypeError(f'Recursive update cannot merge keys with a different type if one is a dictionary. {".".join(new_stack)}')
#                 else:
#                     _recursive_update_map(left[k], v, stack=new_stack)
#                     continue
#         left[k] = v
#
#
# def recursive_update_map(left, right):
#     return _recursive_update_map(left, right, stack=[])
#
#
# # ========================================================================= #
# # Helper                                                                    #
# # ========================================================================= #
#
#
# class attrhelp:
#
#     # double underscores mangle names, however because this is in a
#     # different class it mangles them wrong, according to this class name
#     # dct.__keys becomes dct._attrhelp__keys instead of dct._AttrDict__keys
#
#     @staticmethod
#     def keys(dct):          return dct._AttrMap__keys()        if isinstance(dct, AttrMap) else dct.keys()
#     @staticmethod
#     def values(dct):        return dct._AttrMap__values()      if isinstance(dct, AttrMap) else dct.values()
#     @staticmethod
#     def items(dct):         return dct._AttrMap__items()       if isinstance(dct, AttrMap) else dct.items()
#     @staticmethod
#     def update(dct, other): return dct._AttrMap__update(other) if isinstance(dct, AttrMap) else dct.update(other)
#
#     @staticmethod
#     def recursive_to_dict(value):
#         return _recursive_convert(value, dict_type=dict)
#
#     @staticmethod
#     def recursive_to_attrdict(value):
#         return _recursive_convert(value, dict_type=AttrMap)
#
#
# # ========================================================================= #
# # End                                                                       #
# # ========================================================================= #

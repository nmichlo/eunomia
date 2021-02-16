from glob import glob
import os
import ruamel.yaml as yaml

from eunomia.backend import Backend
from eunomia.backend._backend_dict import normalise_option_dict
from eunomia.config import Group, Option
from eunomia.config.nodes import IgnoreNode


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class BackendYaml(Backend):

    GROUP_TYPE = str
    OPTION_TYPE = str

    def _get_sorted_option_paths(self, root_folder: str):
        ext = '.yaml'
        # get all yaml files
        found_paths = glob(os.path.join(root_folder, f'**/*{ext}'), recursive=True)
        # remove root folder from names
        paths = []
        for path in found_paths:
            # get the relative path, strip the extension, and split
            p = os.path.relpath(path, root_folder)
            p = os.path.splitext(p)[0]
            p = _os_split_path(p)
            # append the path and split path used to sort
            paths.append((path, p))
        # sort paths by length, then alphabetically
        return sorted(paths, key=lambda p: (len(p[1]), *p[1]))

    def _load_group(self, value: GROUP_TYPE) -> Group:
        if not os.path.isdir(value):
            raise FileNotFoundError(f'root_folder={repr(value)} is not a valid directory.\n\tAre you sure the path is correct and not relative?\n\tCurrent working directory is: {repr(os.getcwdb().decode())}')
        # load group
        root = Group()
        for path, (*subgroups, option_name) in self._get_sorted_option_paths(value):
            # add subgroups
            group = root.get_subgroup_recursive(subgroups, make_missing=True)
            # add option by loading file
            group.add_option(option_name, self.load_option(path))
        # done!
        return root

    def _load_option(self, value: OPTION_TYPE) -> Option:
        if not os.path.isfile(value):
            raise FileNotFoundError(f'root_folder={repr(value)} is not a file.\n\tAre you sure the path is correct and not relative?\n\tCurrent working directory is: {repr(os.getcwdb().decode())}')
        if os.path.splitext(value)[1] != '.yaml':
            raise ValueError(f'option file has incorrect extension: {repr(os.path.splitext(value)[1])}, should be a .yaml file')
        # load option
        data = yaml_load_file(value)
        # convert data to option
        return Option.from_dict(normalise_option_dict(data, recursive=False, allow_compact=True))

    def _dump_group(self, group: Group):
        raise RuntimeError('Not implemented!')  # pragma: no cover

    def _dump_option(self, option: Option):
        raise RuntimeError('Not implemented!')  # pragma: no cover


def _os_split_path(path, force_relative=True):
    # get the path
    if force_relative:
        assert not os.path.isabs(path)
    # get the normalised path
    path = os.path.normpath(path)
    # split the path into its keys
    parts, head = [], path
    while True:
        head, tail = os.path.split(head)
        if tail:
            parts.append(tail)
            continue
        elif head:
            parts.append(head)
        break
    parts = parts[::-1]
    # check the path is the original
    recon_path = os.path.join(*parts) if parts else ''
    if recon_path != path:
        raise RuntimeError(f'reconstructed path {repr(recon_path)} is not equal to original {repr(path)}')
    return parts


# ========================================================================= #
# Yaml Loader                                                               #
# ========================================================================= #


class EunomiaSafeLoader(yaml.SafeLoader):

    def __init__(self, *args, always_substitute_strings=True, **kwargs):
        super().__init__(*args, **kwargs)
        # custom config values
        self._always_substitute_strings = always_substitute_strings

    @classmethod
    def add_constructors(cls, tags: list, constructor):
        for tag in tags:
            cls.add_constructor(tag, constructor)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Custom Constructors                                                   #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    # def construct_custom_tuple(self, node: yaml.Node):
    #     if not isinstance(node, yaml.SequenceNode):
    #         raise yaml.YAMLError(f'tag {node.tag} for tuple(...) is not compatible with node: {node.__class__.__name__}. {repr(node.value)} must be a sequence/list')
    #     return tuple(self.construct_sequence(node))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Node Constructors                                                     #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def construct_node_ignore(self, node: yaml.Node):
        if not isinstance(node, yaml.ScalarNode):
            raise TypeError(f'tag {node.tag} for {IgnoreNode.__name__} is not compatible with node: {node.__class__.__name__} which is not a scalar.')
        return IgnoreNode(self.construct_scalar(node))

    # def construct_node_ref(self, node: yaml.Node):
    #     return RefNode(self.construct_yaml_str(node))

    # def construct_node_eval(self, node: yaml.Node):
    #     return EvalNode(self.construct_yaml_str(node))

    # def construct_node_sub(self, node: yaml.Node):
    #     return SubNode(self.construct_yaml_str(node))


# EunomiaSafeLoader.add_constructors(['!tuple'], EunomiaSafeLoader.construct_custom_tuple)
EunomiaSafeLoader.add_constructors(['!str'], EunomiaSafeLoader.construct_node_ignore)
# EunomiaSafeLoader.add_constructors(['!ref'], EunomiaSafeLoader.construct_node_ref)
# EunomiaSafeLoader.add_constructors(['!expr'], EunomiaSafeLoader.construct_node_eval)
# EunomiaSafeLoader.add_constructors(['!sub'], EunomiaSafeLoader.construct_node_sub)


# NOTE: unknown tags can be parsed
#       - https://github.com/kislyuk/yq/blob/2dd5cf39e18f2caf0c416e3da1c93a62bc801e0b/yq/loader.py#L57
# TODO: hydra adds the following implicit_resolvers & filters them
#       - float: https://github.com/omry/omegaconf/blob/ad593a527556583dfefa6d7dd34beec3f183a438/omegaconf/_utils.py#L106
#       - timestamp: https://github.com/omry/omegaconf/blob/ad593a527556583dfefa6d7dd34beec3f183a438/omegaconf/_utils.py#L120


# ========================================================================= #
# Yaml Util                                                                 #
# ========================================================================= #


def yaml_load(string):
    return yaml.load(string, EunomiaSafeLoader, version='1.2')


def yaml_load_file(path):
    with open(path, 'r') as f:
        return yaml_load(f.read())


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

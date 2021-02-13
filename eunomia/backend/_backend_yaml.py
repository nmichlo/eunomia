from glob import glob
import os
import ruamel.yaml as yaml

from eunomia.backend import Backend
from eunomia.config import Group, Option
from eunomia.config.nodes import IgnoreNode, RefNode, EvalNode, SubNode
from eunomia.config import scheme as s


# ========================================================================= #
# Config Backend                                                            #
# ========================================================================= #


class BackendYaml(Backend):

    def __init__(self, root_folder: str):
        # check the root folder
        if not isinstance(root_folder, str):
            raise TypeError(f'root_folder={repr(root_folder)} must be a string')
        if not os.path.isdir(root_folder):
            raise FileNotFoundError(f'root_folder={repr(root_folder)} is not a valid directory.\n\tAre you sure the path is correct and not relative?\n\tCurrent working directory is: {repr(os.getcwdb().decode())}')
        self._root_folder = root_folder        # loading modes

    @staticmethod
    def _norm_split_path(path, force_relative=True):
        path = os.path.normpath(path)
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
        recon_path = os.path.join(*parts) if parts else ''
        assert recon_path == path, f'reconstructed path {repr(recon_path)} is not equal to original {repr(path)}'
        if force_relative:
            assert not os.path.isabs(path)
        return parts

    def _get_sorted_paths(self):
        ext = '.yaml'
        # get all yaml files
        found_paths = glob(os.path.join(self._root_folder, f'**/*{ext}'), recursive=True)
        # remove root folder from names
        paths = []
        for path in found_paths:
            # get the relative path
            p = os.path.relpath(path, self._root_folder)
            # strip the extension
            p = os.path.splitext(p)[0]
            # split the path
            p = self._norm_split_path(p)
            # append the path and split path used to sort
            paths.append((path, p))
        # sort paths by length, then alphabetically
        return sorted(paths, key=lambda p: (len(p[1]), *p[1]))

    def _option_from_compact_dict(self, data):
        if s.KEY_DATA in data:
            return Option.from_dict(data)
        else:
            # pop all config values
            pkg = data.pop(s.KEY_PKG, None)
            merge = data.pop(s.KEY_MERGE, None)
            type = data.pop(s.KEY_TYPE, None)
            # check that we have nothing extra
            if any(k in s.RESERVED_KEYS for k in data.keys()):
                raise KeyError(f'A reserved key was found in a compact option dictionary: {list(k for k in data.keys() if k in s.RESERVED_KEYS)}')
            # no need to validate because of above
            return Option(pkg=pkg, include=merge, data=data)

    def _load_root_group(self) -> Group:
        root = Group()
        for path, (*subgroups, option_name) in self._get_sorted_paths():
            # add subgroups
            group = root.get_subgroups_recursive(subgroups, make_missing=True)
            # add option by loading file
            data = yaml_load_file(path)
            group.add_option(option_name, self._option_from_compact_dict(data))
        # done!
        return root


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

    def construct_custom_tuple(self, node: yaml.Node):
        if not isinstance(node, yaml.SequenceNode):
            raise yaml.YAMLError(f'tag {node.tag} for tuple(...) is not compatible with node: {node.__class__.__name__}. {repr(node.value)} must be a sequence/list')
        return tuple(self.construct_sequence(node))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
    # Node Constructors                                                     #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

    def construct_node_ignore(self, node: yaml.Node):
        if not isinstance(node, yaml.ScalarNode):
            raise TypeError(f'tag {node.tag} for {IgnoreNode.__name__} is not compatible with node: {node.__class__.__name__} which is not a scalar.')
        return IgnoreNode(self.construct_scalar(node))

    def construct_node_ref(self, node: yaml.Node):
        return RefNode(self.construct_yaml_str(node))

    def construct_node_eval(self, node: yaml.Node):
        return EvalNode(self.construct_yaml_str(node))

    def construct_node_sub(self, node: yaml.Node):
        return SubNode(self.construct_yaml_str(node))


EunomiaSafeLoader.add_constructors(['!tuple'], EunomiaSafeLoader.construct_custom_tuple)
EunomiaSafeLoader.add_constructors(['!str'], EunomiaSafeLoader.construct_node_ignore)
EunomiaSafeLoader.add_constructors(['!ref'], EunomiaSafeLoader.construct_node_ref)
EunomiaSafeLoader.add_constructors(['!expr'], EunomiaSafeLoader.construct_node_eval)
EunomiaSafeLoader.add_constructors(['!sub'], EunomiaSafeLoader.construct_node_sub)


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

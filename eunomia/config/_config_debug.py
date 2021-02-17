import re
from typing import Union as _Union
from eunomia.config._config import _ConfigObject, Group, Option
from eunomia.config.nodes import ConfigNode
from eunomia.config import validate as V


# ========================================================================= #
# debug tree                                                                #
# ========================================================================= #


def debug_tree_print(root: _Union[Group, Option], colors=True, show_options=True, full_option_path=True, full_group_path=True, show_defaults=True):
    print(debug_tree_str(
        root=root, colors=colors, show_options=show_options, full_option_path=full_option_path,
        full_group_path=full_group_path, show_defaults=show_defaults
    ))


def debug_tree_str(root: _Union[Group, Option], colors=True, show_options=True, full_option_path=True, full_group_path=True, show_defaults=True):
    from attr import dataclass

    @dataclass
    class _WalkObj:
        node: _ConfigObject
        visited: bool
        is_last: bool
        @property
        def is_group(self):
            return isinstance(self.node, Group)
        @property
        def has_groups_after(self):
            return self.node.has_parent and isinstance(self.node.parent, Group) and bool(self.node.parent.groups)
        @property
        def key(self):
            return (self.is_group, self.visited, self.is_last, self.has_groups_after)
        def __str__(self):
            return f":{''.join(map(str, map(int, self.key)))}"

    def _is_last_iter(items):
        yield from ((item, i == len(items ) -1) for i, item in enumerate(items))

    def _walk():
        def _recurse(node, is_last, stack):
            stk = stack + [_WalkObj(node, False, is_last)]
            yield stk
            stk[-1].visited = True
            if isinstance(node, Group):
                if show_options:
                    for o, l in _is_last_iter(node.options.values()):
                        yield from _recurse(o, l, stk)
                for g, l in _is_last_iter(node.groups.values()):
                    yield from _recurse(g, l, stk)
        return _recurse(root, True, [])

    if colors:
        nG, nO, S, G, O, R = '\033[35m', '\033[33m', '\033[90m', '\033[95m', '\033[93m', '\033[0m'
    else:
        nG, nO, S, G, O, R = '', '', '', '', '', ''

    TREE = {
        (1, 1, 1, 0): f'   ',           # group,  visited,   last,  has groups after
        (1, 1, 1, 1): f'   ',           # group,  visited,   last,  no groups after
        (1, 0, 1, 0): f'   ',           # group,  unvisited, last,  has groups after
        (1, 1, 0, 1): f' {S}│{R} ',     # group,  visited,   inner, no groups after
        (1, 0, 0, 1): f' {S}├{G}─{R}',  # group,  unvisited, inner, no groups after
        (1, 0, 1, 1): f' {S}╰{G}─{R}',  # group,  unvisited, last,  no groups after
        (0, 0, 0, 1): f' {S}│{R} ',     # option, unvisited, last,  has groups after
        (0, 0, 1, 1): f' {S}├{O}╌{R}',  # option, unvisited, last,  no groups after
        (0, 0, 0, 0): f' {S}├{O}╌{R}',  # option, unvisited, inner, has groups after
        (0, 0, 1, 0): f' {S}╰{O}╌{R}',  # option, unvisited, last,  has groups after
    }

    # get correct line length without ansi colors
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    lengths, lines, items = {}, [], []
    for stack in _walk():
        (*_, item) = stack
        tree = ''.join(TREE.get(o.key, f'ERR{o}') for o in stack[1:])
        if item.is_group:
            # GROUP
            keys = [f'/{k}' for k in (item.node.keys if item.node.keys else ('',))]
            name = f"{nG}{keys[-1]}{R}"
            if full_group_path:
                name = f"{S}{''.join(keys[:-1])}{R}" + name
        else:
            # OPTION
            name = f"{nO}{item.node.key}{R}"
            if full_option_path:
                name = f"{S}{('/' + '/'.join(item.node.keys[:-1]))}:{R} " + name
        # append for next iterations
        line = f'{tree} {name}'
        # get max line length
        lengths.setdefault(item.node.parent, 0)
        lengths[item.node] = len(ansi_escape.sub('', line))
        lengths[item.node.parent] = max(lengths[item.node.parent], lengths[item.node])
        # append
        lines.append(line)
        items.append(item)

    def get_defaults(option):
        for default in V.split_defaults_list_items(option.get_unresolved_defaults(), allow_config_node_return=True):
            if isinstance(default, Option):
                yield f'{default.abs_group_path}: {default.key}'
            elif isinstance(default, tuple):
                yield f'{str(default[0])}: {str(default[1])}'
            elif isinstance(default, ConfigNode):
                yield str(default)
            else:
                yield str(default)

    if show_defaults:
        new_lines = []
        for line, item in zip(lines, items):
            if not item.is_group:
                defaults = list(get_defaults(item.node))
                if defaults:
                    padding = lengths[item.node.parent] - lengths[item.node]
                    line = f'{line}{" "*padding} {S}[{", ".join(defaults)}]{R}'
            new_lines.append(line)
        lines = new_lines

    return '\n'.join(lines)


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

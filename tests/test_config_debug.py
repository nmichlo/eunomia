import re

from eunomia.config.nodes import SubNode

from tests.test_backend_obj import _make_config_group
from tests.util import temp_capture_stdout


# ========================================================================= #
# Test Config Objects                                                       #
# ========================================================================= #


def test_debug_groups():
    root = _make_config_group(suboption='suboption1')

    with temp_capture_stdout() as out:
        root.debug_tree_print()
    color_out = out.getvalue()
    assert color_out == ' \x1b[90m\x1b[0m\x1b[35m/\x1b[0m\n \x1b[90m├\x1b[93m╌\x1b[0m \x1b[90m/:\x1b[0m \x1b[33mdefault\x1b[0m\n \x1b[90m├\x1b[95m─\x1b[0m \x1b[90m\x1b[0m\x1b[35m/subgroup\x1b[0m\n \x1b[90m│\x1b[0m  \x1b[90m├\x1b[93m╌\x1b[0m \x1b[90m/subgroup:\x1b[0m \x1b[33msuboption1\x1b[0m\n \x1b[90m│\x1b[0m  \x1b[90m╰\x1b[93m╌\x1b[0m \x1b[90m/subgroup:\x1b[0m \x1b[33msuboption2\x1b[0m\n \x1b[90m╰\x1b[95m─\x1b[0m \x1b[90m\x1b[0m\x1b[35m/subgroup2\x1b[0m\n    \x1b[90m╰\x1b[95m─\x1b[0m \x1b[90m/subgroup2\x1b[0m\x1b[35m/subgroup3\x1b[0m\n       \x1b[90m├\x1b[93m╌\x1b[0m \x1b[90m/subgroup2/subgroup3:\x1b[0m \x1b[33msub2option1\x1b[0m\n       \x1b[90m╰\x1b[93m╌\x1b[0m \x1b[90m/subgroup2/subgroup3:\x1b[0m \x1b[33msub2option2\x1b[0m\n'

    with temp_capture_stdout() as out:
        root.debug_tree_print(colors=False)
    normal_out = out.getvalue()
    assert normal_out == ' /\n ├╌ /: default\n ├─ /subgroup\n │  ├╌ /subgroup: suboption1\n │  ╰╌ /subgroup: suboption2\n ╰─ /subgroup2\n    ╰─ /subgroup2/subgroup3\n       ├╌ /subgroup2/subgroup3: sub2option1\n       ╰╌ /subgroup2/subgroup3: sub2option2\n'
    # https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
    assert normal_out == re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', color_out)

    with temp_capture_stdout() as out:
        root.debug_tree_print(colors=False, show_defaults=True)
    normal_out_defaults = out.getvalue()
    assert normal_out_defaults == ' /\n ├╌ /: default [subgroup: suboption1]\n ├─ /subgroup\n │  ├╌ /subgroup: suboption1\n │  ╰╌ /subgroup: suboption2\n ╰─ /subgroup2\n    ╰─ /subgroup2/subgroup3\n       ├╌ /subgroup2/subgroup3: sub2option1\n       ╰╌ /subgroup2/subgroup3: sub2option2\n'

    root = _make_config_group(suboption=SubNode('suboption${=1}'))
    with temp_capture_stdout() as out:
        root.debug_tree_print(colors=False, show_defaults=True)
    normal_out_defaults_special = out.getvalue()
    assert normal_out_defaults_special == ' /\n ├╌ /: default [subgroup: suboption${=1}]\n ├─ /subgroup\n │  ├╌ /subgroup: suboption1\n │  ╰╌ /subgroup: suboption2\n ╰─ /subgroup2\n    ╰─ /subgroup2/subgroup3\n       ├╌ /subgroup2/subgroup3: sub2option1\n       ╰╌ /subgroup2/subgroup3: sub2option2\n'

    # TODO: test other flags and suboption cases


# ========================================================================= #
# END                                                                       #
# ========================================================================= #

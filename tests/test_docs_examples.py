import pytest

from tests.util import temp_capture_stdout, temp_wd, to_import_path, path_from_root, read_from_root

TESTS = [
    ('docs/examples/quickstart', 'simple_yaml'),
    ('docs/examples/quickstart', 'simple_yaml_alt'),
    ('docs/examples/quickstart', 'simple_pythonic'),
    ('docs/examples/quickstart', 'advanced_yaml'),
]


@pytest.mark.parametrize(["folder", "name"], TESTS)
def test_docs_examples_eval_to_targets(folder, name):
    # get test files
    import_path = to_import_path(path_from_root(folder, f'example_{name}.py'))
    target_file = path_from_root(folder, f'target_{name}')
    # run all the files in the examples folder
    import importlib
    with temp_wd(folder):
        with temp_capture_stdout() as f:
            importlib.import_module(import_path)
    assert f.getvalue() == read_from_root(target_file)

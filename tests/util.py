import os
import sys
from contextlib import contextmanager
from io import StringIO


@contextmanager
def temp_no_stdout():
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    yield
    sys.stdout = old_stdout


@contextmanager
def temp_capture_stdout() -> StringIO:
    old_stdout, temp_out = sys.stdout, StringIO()
    sys.stdout = temp_out
    yield temp_out
    sys.stdout = old_stdout


class temp_wd:
    def __init__(self, new_wd):
        self._new_wd = os.path.normpath(os.path.abspath(new_wd))
        self._old_wd = None
    def __enter__(self):
        self._old_wd = os.getcwd()
        os.chdir(self._new_wd)
    def __exit__(self, exc_type, exc_val, exc_tb):
        # @contextmanager versions do not
        # run statements after yield on failure
        os.chdir(self._old_wd)
        self._old_wd = None


def path_from_root(*parts):
    # we dont use os.getcwd in case the wd has changed!
    root = os.path.dirname(os.path.dirname(__file__))
    root = os.path.normpath(os.path.join(root, *parts))
    return root


def read_from_root(*parts: str) -> str:
    with open(path_from_root(*parts), 'r') as f:
        return f.read()


def to_import_path(path: str):
    assert path.endswith('.py')
    path = path[:-len('.py')]
    path = os.path.abspath(os.path.normpath(path))
    path = os.path.relpath(path, os.getcwd())
    return '.'.join(path.split('/'))

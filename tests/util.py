import os
import sys
from contextlib import contextmanager
from io import StringIO


@contextmanager
def no_stdout():
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    yield
    sys.stdout = old_stdout


@contextmanager
def capture_stdout():
    old_stdout, temp_out = sys.stdout, StringIO()
    sys.stdout = temp_out
    yield temp_out
    sys.stdout = old_stdout


def get_tests_path(*parts):
    return os.path.normpath(os.path.join(os.path.dirname(__file__), *parts))

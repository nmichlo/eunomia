
# mkdocs-simple-hooks 0.1.2 is buggy and hooks can't be
# nested more than two packages deep.
# eg. `docs.src:on_nav` works but `docs.src.hooks:on_nav` does not!
from ._hooks import on_nav

from typing import Union
from mkdocs.structure.nav import Navigation, Section, Page


# ========================================================================= #
# Vars                                                                      #
# ========================================================================= #


# meta tags
META_TAG_EXCLUDE = 'hidden'
META_TAG_POS = 'pos'
META_TAG_SECTION_EXCLUDE = 'section_hidden'
META_TAG_SECTION_POS = 'section_pos'
META_TAG_SECTION_TITLE = 'section_title'

# added attrs to nav nodes
ATTR_EXCLUDE = '_nav_hook_exclude'
ATTR_POS_KEY = '_nav_hook_pos_key'


# ========================================================================= #
# Entry Point                                                               #
# ========================================================================= #


def on_nav(nav: Navigation, config, files):
    _recursive_modify(nav, config)
    return nav


# ========================================================================= #
# Helper                                                                    #
# ========================================================================= #


def _get_pos_meta(dct: dict, key: str, is_section: bool):
    pos = dct.get(key, None)
    if pos is None:
        pos_type, pos = 0, 0
    else:
        assert isinstance(pos, (int, float)), f'meta tag {key}={repr(pos)}'
        pos_type, pos = (-1 if pos >= 0 else 1), pos
    pos_key = (bool(is_section), pos_type, pos)
    return pos_key


def _get_exclude_meta(dct: dict, key: str):
    exclude = dct.get(key, False)
    assert isinstance(exclude, bool), f'meta tag {key}={repr(exclude)} must be a boolean value'
    return exclude


def _get_title_meta(dct: dict, key: str):
    title = dct.get(key, None)
    if title is not None:
        assert isinstance(title, str), f'meta tag {key}={repr(title)} must be a string'
    return title


def _sort_and_filter_sections_and_pages(items):
    items = filter(lambda x: not getattr(x, ATTR_EXCLUDE), items)
    items = sorted(items, key=lambda x: getattr(x, ATTR_POS_KEY))
    return items


# ========================================================================= #
# Modify                                                                    #
# ========================================================================= #


def _modify_nav(nav: Navigation):
    assert isinstance(nav, Navigation)
    # do reorder after nav meta is set
    nav.items = _sort_and_filter_sections_and_pages(nav.items)


def _modify_section(section: Section):
    assert isinstance(section, Section)
    # ================================
    # get default values
    setattr(section, ATTR_EXCLUDE, _get_exclude_meta({}, 'N/A'))
    setattr(section, ATTR_POS_KEY, _get_pos_meta({}, 'N/A', is_section=True))
    # copy exclude / key information from first index page
    for page in section.children:
        if isinstance(page, Page) and page.is_index:
            setattr(section, ATTR_EXCLUDE, _get_exclude_meta(page.meta, key=META_TAG_SECTION_EXCLUDE))
            setattr(section, ATTR_POS_KEY, _get_pos_meta(page.meta, key=META_TAG_SECTION_POS, is_section=True))
            section.title = _get_title_meta(page.meta, key=META_TAG_SECTION_TITLE)
            break
    # if there are no shown children, hide the section!
    all_children_excluded = all(getattr(child, ATTR_EXCLUDE) for child in section.children)
    # update exclude attr
    setattr(section, ATTR_EXCLUDE, getattr(section, ATTR_EXCLUDE) or all_children_excluded)
    # ================================
    # do reorder after nav meta is set
    section.children = _sort_and_filter_sections_and_pages(section.children)


def _modify_page(page: Page, config):
    assert isinstance(page, Page)
    # read values -- this might mess things up, child values might need to be reset after calling this.
    page.read_source(config)
    # get metadata
    setattr(page, ATTR_EXCLUDE, _get_exclude_meta(page.meta, key=META_TAG_EXCLUDE))
    setattr(page, ATTR_POS_KEY, _get_pos_meta(page.meta, key=META_TAG_POS, is_section=False))



# ========================================================================= #
# Recurse                                                                   #
# ========================================================================= #


def _recursive_modify(item: Union[Navigation, Section, Page], config):
    if isinstance(item, Navigation):
        for i in item.items:
            _recursive_modify(i, config)
        _modify_nav(item)
    elif isinstance(item, Section):
        for i in item.children:
            _recursive_modify(i, config)
        _modify_section(item)
    elif isinstance(item, Page):
        _modify_page(item, config)
    else:
        raise RuntimeError(f'Unknown type: {type(item)} -- {item}')


# ========================================================================= #
# End                                                                       #
# ========================================================================= #

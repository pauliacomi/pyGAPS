# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
from unittest.mock import MagicMock


# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only set the theme if we're building docs locally
    html_theme = 'sphinx_rtd_theme'


# Need to mock modules using MagicMock, or else they won't be able to
# be installed on readthedocs
class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()


MOCK_MODULES = ['matplotlib', 'matplotlib.pyplot', 'matplotlib.ticker',
                'numpy', 'pandas', 'scipy', 'scipy.constants', 'scipy.stats',
                'scipy.optimize', 'scipy.interpolate']
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)


# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'nbsphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.extlinks',
    'sphinx.ext.ifconfig',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
]
# If currently spellchecking
if os.getenv('SPELLCHECK'):
    extensions += 'sphinxcontrib.spelling',
    spelling_show_suggestions = True
    spelling_lang = 'en_US'


# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'pygaps'
year = '2018'
author = 'Paul Iacomi'
copyright = '{0}, {1}'.format(year, author)
version = release = '1.3.0'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['.']

# Needed for jupyter notebook compilation by nbsphinx
exclude_patterns = ['_build', '**.ipynb_checkpoints']

# Needed for jupyter notebook compilation by nbsphinx
pygments_style = 'trac'

# Suppressing the nonlocal_uri image warning, as it appears due to
# github badges being stored on another server
suppress_warnings = ['image.nonlocal_uri']

# External links
extlinks = {
    'issue': ('https://github.com/pauliacomi/pygaps/issues/%s', '#'),
    'pr': ('https://github.com/pauliacomi/pygaps/pull/%s', 'PR #'),
}

linkcheck_ignore = [
    r'https://github.com/pauliacomi/pygaps/compare/.+',
]

# Checking for internal links
nitpicky = True

# -- Options for HTML output ---------------------------------------------------

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "logo.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = 'favicon.ico'

html_last_updated_fmt = '%b %d, %Y'
html_split_index = False
html_sidebars = {
    '**': ['searchbox.html', 'globaltoc.html', 'sourcelink.html'],
}
html_short_title = '%s-%s' % (project, version)


# -- napoleon configuration -----------------------------------------------------

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False

# -- autodoc configuration -----------------------------------------------------

autodoc_member_order = 'bysource'
autodoc_mock_imports = ['_tkinter']

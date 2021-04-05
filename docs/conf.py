# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
from unittest.mock import MagicMock

# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only set the theme if we're building docs locally
    html_theme = 'sphinx_rtd_theme'


# Need to mock modules using MagicMock, as they won't be able to
# be installed on readthedocs
class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()


MOCK_MODULES = [
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.ticker',
    'matplotlib.cm',
    'numpy',
    'pandas',
    'pandas.util',
    'scipy',
    'scipy.constants',
    'scipy.stats',
    'scipy.optimize',
    'scipy.interpolate',
    'scipy.integrate',
    'coolprop',
]
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
year = '2021'
author = 'Paul Iacomi'
copyright = '{0}, {1}'.format(year, author)
try:
    from importlib.metadata import version as imp_version
    version = release = imp_version("pygaps")
except ModuleNotFoundError:
    from pkg_resources import get_distribution as imp_version
    version = release = imp_version("pygaps").version

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

linkcheck_timeout = 3
linkcheck_retries = 2
linkcheck_ignore = [
    r'https://github.com/pauliacomi/pygaps/compare/.+',
    r'https://requires.io/.+',
    r'https://twitter.com/.+',
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

# -- nbsphinx configuration -----------------------------------------------------

nbsphinx_prolog = r"""
{% set docname = 'docs/' + env.doc2path(env.docname, base=None) %}

.. raw:: html

    <div class="admonition note">
      This page was generated from
      <a class="reference external" href="https://github.com/pauliacomi/pyGAPS/blob/v{{ env.config.release|e }}/{{ docname|e }}">{{ docname|e }}</a>.
      An interactive online version can be started on Binder:
      <span style="white-space: nowrap;"><a href="https://mybinder.org/v2/gh/pauliacomi/pyGAPS/v{{ env.config.release|e }}?filepath={{ docname|e }}"><img alt="Binder badge" src="https://mybinder.org/badge_logo.svg" style="vertical-align:text-bottom"></a>.</span>
      <script>
        if (document.location.host) {
          $(document.currentScript).replaceWith(
            '<a class="reference external" ' +
            'href="https://nbviewer.jupyter.org/url' +
            (window.location.protocol == 'https:' ? 's/' : '/') +
            window.location.host +
            window.location.pathname.slice(0, -4) +
            'ipynb">View in <em>nbviewer</em></a> instead.'
          );
        }
      </script>
    </div>
"""

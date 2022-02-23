"""Configuration for documentation building"""
# -- Init -----------------------------------------------------

import os
import sys
from unittest.mock import MagicMock

# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

# if not on_rtd:  # only set the theme if we're building docs locally
html_theme = "furo"


# -- Mocking of modules -----------------------------------------------------
# Need to mock most modules using MagicMock, as they won't be able to
# be installed on ReadTheDocs
class Mock(MagicMock):
    """Simple mock class."""
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()


MOCK_MODULES = [
    #     'matplotlib',
    #     'matplotlib.pyplot',
    #     'matplotlib.ticker',
    #     'matplotlib.cm',
    #     'matplotlib.rc_context',
    #     'numpy',
    #     'pandas',
    #     'pandas.util',
    #     'scipy',
    #     'scipy.constants',
    #     'scipy.stats',
    #     'scipy.optimize',
    #     'scipy.interpolate',
    #     'scipy.integrate',
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
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
    'sphinx.ext.intersphinx',
    'sphinx_copybutton',
]
# If currently spellchecking
if os.getenv('SPELLCHECK'):
    extensions += 'sphinxcontrib.spelling'
    spelling_show_suggestions = True
    spelling_lang = 'en_UK'

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'pyGAPS'
year = '2022'
author = 'Paul Iacomi'
copyright = f'{year}, {author}'
try:
    from importlib.metadata import version as imp_version
    version = release = imp_version("pygaps")
except ModuleNotFoundError:
    from pkg_resources import get_distribution as imp_version
    version = release = imp_version("pygaps").version

print(project, " version defined as ", version)

# Needed for jupyter notebook compilation by nbsphinx
exclude_patterns = [
    '_build',
    '**.ipynb_checkpoints',
]

# Style of code colorization
pygments_style = 'manni'
pygments_dark_style = 'dracula'

# Suppressing the nonlocal_uri image warning, as it appears due to
# github badges being stored on another server
suppress_warnings = [
    'image.nonlocal_uri',
]

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
    r'https://www.coolprop.org/.+',
]

# Checking for internal links
nitpicky = True
nitpick_ignore = [
    ('py:class', 'numpy.ndarray'),
    ('py:class', 'pandas.core.frame.DataFrame'),
    ('py:class', 'pandas.core.series.Series'),
]

# -- Options for HTML output ---------------------------------------------------

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "logo.svg"

# The name of an image file (within the static path) to use as favicon of the
# docs. This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = 'favicon.ico'

# Custom CSS/JS
html_static_path = ["_static"]
html_css_files = [
    'css/custom.css',
]
# html_js_files = [
#     'js/darkmode.js',
# ]

# Others
html_last_updated_fmt = '%b %d, %Y'
html_split_index = False
# html_sidebars = {
#     '**': ['searchbox.html', 'globaltoc.html', 'sourcelink.html'],
# }
html_short_title = f"{project}-{version}"

# Other options
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "announcement":
    "A <a href=\"https://github.com/pauliacomi/pyGAPS-gui\" >graphical user interface</a> for pyGAPS is now available!",
    "light_css_variables": {
        "color-brand-primary": "#c2389e",
        "color-background-secondary": "#f0fbff",
        "color-announcement-background": "#5d0f60",
    },
    "dark_css_variables": {
        "color-brand-primary": "#c2389e",
        "color-background-primary": "#151420",
        "color-background-secondary": "#1a1d25",
        "color-announcement-background": "#5d0f60",
        "color-admonition-background": "#190242",
    },
}

# -- autodoc configuration -----------------------------------------------------
# parse docstrings as documentation

autodoc_member_order = 'bysource'
autodoc_mock_imports = []
autodoc_typehints = 'signature'
autodoc_typehints_format = 'short'

# -- napoleon configuration -----------------------------------------------------
# parse numpy-style docstrings

napoleon_numpy_docstring = True
napoleon_google_docstring = False
napoleon_use_ivar = True
napoleon_use_param = False
napoleon_use_rtype = False
napoleon_use_admonition_for_references = False

# -- nbsphinx configuration -----------------------------------------------------
# allows parsing of Jupyter notebooks to docs

nbsphinx_prolog = r"""
{% set docname = 'docs/' + env.doc2path(env.docname, base=None) %}

.. raw:: html

    <div class="admonition note">
      This page was generated from
      <a class="reference external" href="https://github.com/pauliacomi/pyGAPS/blob/v{{ env.config.release|e }}/{{ docname|e }}">{{ docname|e }}</a>.
      To start an interactive version:
      <span style="white-space: nowrap;"><a href="https://mybinder.org/v2/gh/pauliacomi/pyGAPS/v{{ env.config.release|e }}?filepath={{ docname|e }}"><img alt="Binder badge" src="https://mybinder.org/badge_logo.svg" style="vertical-align:text-bottom"></a></span>
      <script>
        if (document.location.host) {
          $(document.currentScript).replaceWith(
            '<a class="reference external" ' +
            'href="https://nbviewer.jupyter.org/url' +
            (window.location.protocol == 'https:' ? 's/' : '/') +
            window.location.host +
            window.location.pathname.slice(0, -4) +
            'ipynb">or view in <em>nbviewer</em></a> instead.'
          );
        }
      </script>
    </div>
"""

# -- intersphinx configuration --------------------------------------------------
# allows to link to other documentations
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

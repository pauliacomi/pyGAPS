# pylint: disable=W0614,W0611,W0622
# flake8: noqa
# isort:skip_file

__author__ = 'Paul Iacomi'
__docformat__ = 'restructuredtext'

try:
    from ._version import version
    __version__ = version
except:
    __version__ = '3.1.0'

import sys
import logging
import warnings
logger = logging.getLogger('pygaps')
logger.setLevel(logging.DEBUG)

# create console handler
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.INFO)

# add the handlers to the logger
logger.addHandler(ch)

# This code is written for Python 3.
if sys.version_info[0] != 3:
    logger.error("pyGAPS requires Python 3.")
    sys.exit(1)

# Let users know if they're missing any hard dependencies
hard_dependencies = ("numpy", "pandas", "scipy")
soft_dependencies = {
    "CoolProp": "Used for many thermodynamic backend calculations."
}
missing_dependencies = []

import importlib
for dependency in hard_dependencies:
    if not importlib.util.find_spec(dependency):
        missing_dependencies.append(dependency)

if missing_dependencies:
    raise ImportError(f"Missing required dependencies {missing_dependencies}")

for dependency in soft_dependencies:
    if not importlib.util.find_spec(dependency):
        warnings.warn(
            f"Missing important package {dependency}. {soft_dependencies[dependency]}"
        )

del hard_dependencies, soft_dependencies, dependency, missing_dependencies


# This lazy load function will be used for non-critical modules to speed import time
# Examples: matplotlib, scipy.optimize
def _load_lazy(fullname):
    try:
        return sys.modules[fullname]
    except KeyError:
        spec = importlib.util.find_spec(fullname)
        if not spec:
            raise ModuleNotFoundError(f"Could not import {fullname}.")
        loader = importlib.util.LazyLoader(spec.loader)
        module = importlib.util.module_from_spec(spec)
        # Make module with proper locking and get it inserted into sys.modules.
        loader.exec_module(module)
        sys.modules[fullname] = module
        return module


class scipy_backend():
    """A backend for scipy, which will be lazy loaded."""
    def __init__(self):
        self.optimize = _load_lazy('scipy.optimize')
        self.integrate = _load_lazy('scipy.integrate')
        self.interp = _load_lazy('scipy.interpolate')
        self.stats = _load_lazy('scipy.stats')
        self.const = _load_lazy('scipy.constants')


scipy = scipy_backend()

# Data
from .data import DATABASE
from .data import ADSORBATE_LIST
from .data import MATERIAL_LIST
from .data import load_data

# Thermodynamic backend
from .utilities.coolprop_utilities import thermodynamic_backend
from .utilities.coolprop_utilities import backend_use_coolprop
from .utilities.coolprop_utilities import backend_use_refprop

# Core classes
from .core.adsorbate import Adsorbate
from .core.material import Material
from .core.pointisotherm import PointIsotherm
from .core.modelisotherm import ModelIsotherm

# Data load
load_data()

# Other user-facing functions
from .api import *

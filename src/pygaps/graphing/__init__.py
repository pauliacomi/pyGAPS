# pylint: disable=W0614,W0401,W0611,W0622
# flake8: noqa

import importlib
import sys


def lazy(fullname):
    try:
        return sys.modules[fullname]
    except KeyError:
        spec = importlib.util.find_spec(fullname)
        module = importlib.util.module_from_spec(spec)
        loader = importlib.util.LazyLoader(spec.loader)
        # Make module with proper locking and get it inserted into sys.modules.
        loader.exec_module(module)
        return module


class mpl_backend():
    """A backend for matplotlib, which will be lazy loaded eventually."""
    def __init__(self):
        self.pyplot = importlib.import_module('matplotlib.pyplot')
        self.ticker = importlib.import_module('matplotlib.ticker')
        self.cm = importlib.import_module('matplotlib.cm')


plt = mpl_backend()

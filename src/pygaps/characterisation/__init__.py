# pylint: disable=W0614,W0401,W0611,W0622
# flake8: noqa

from .. import _load_lazy


class scipy_backend():
    """A backend for matplotlib, which will be lazy loaded eventually."""
    def __init__(self):
        self.optimize = _load_lazy('scipy.optimize')
        self.integrate = _load_lazy('scipy.integrate')
        self.stats = _load_lazy('scipy.stats')


scipy = scipy_backend()

# sp_optimize = _load_lazy('scipy.optimize')
# sp_integrate = _load_lazy('scipy.integrate')
# sp_stats = _load_lazy('scipy.stats')

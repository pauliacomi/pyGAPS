# pylint: disable=W0614,W0401,W0611,W0622
# flake8: noqa

from .. import _load_lazy


class mpl_backend():
    """A backend for matplotlib, which will be lazy loaded eventually."""
    def __init__(self):
        pass
        # self.pyplot = _load_lazy('matplotlib.pyplot')
        # self.ticker = _load_lazy('matplotlib.ticker')
        # self.cm = _load_lazy('matplotlib.cm')

    @property
    def pyplot(self):
        import matplotlib.pyplot as plt
        return plt

    @property
    def ticker(self):
        import matplotlib.ticker as tick
        return tick

    @property
    def cm(self):
        import matplotlib.cm as cm
        return cm


plt = mpl_backend()

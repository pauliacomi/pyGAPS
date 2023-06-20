import functools
import inspect

import matplotlib
from matplotlib.testing.decorators import _cleanup_cm


def mpl_cleanup(style=None):
    """
    A decorator to ensure that any global state is reset before
    running a test.

    Parameters
    ----------
    style : str, dict, or list, optional
        The style(s) to apply.  Defaults to ``["classic",
        "_classic_test_patch"]``.
    """

    # If cleanup is used without arguments, *style* will be a callable, and we
    # pass it directly to the wrapper generator.  If cleanup if called with an
    # argument, it is a string naming a style, and the function will be passed
    # as an argument to what we return.  This is a confusing, but somewhat
    # standard, pattern for writing a decorator with optional arguments.

    def make_cleanup(func):
        if inspect.isgeneratorfunction(func):

            @functools.wraps(func)
            def wrapped_callable(*args, **kwargs):
                with _cleanup_cm(), matplotlib.style.context(style):
                    yield from func(*args, **kwargs)
        else:

            @functools.wraps(func)
            def wrapped_callable(*args, **kwargs):
                with _cleanup_cm(), matplotlib.style.context(style):
                    func(*args, **kwargs)

        return wrapped_callable

    if callable(style):
        result = make_cleanup(style)
        # Default of mpl_test_settings fixture and image_comparison too.
        style = ["classic", "_classic_test_patch"]
        return result
    else:
        return make_cleanup

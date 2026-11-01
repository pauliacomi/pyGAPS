import copy
import functools
import inspect
import warnings
from contextlib import contextmanager

import matplotlib
from matplotlib import pyplot
from matplotlib import style as mpl_style
from matplotlib import units

import pygaps
from pygaps.utilities import coolprop_utilities


@contextmanager
def isolated_pygaps_state():
    """Restore registry containers and serializable fields without copying native states."""
    registries = [(registry, list(registry)) for registry in (pygaps.MATERIAL_LIST, pygaps.ADSORBATE_LIST)]
    backend = pygaps.thermodynamic_backend()
    snapshots = []
    for registry, members in registries:
        for item in members:
            aliases = item.alias if isinstance(item, pygaps.Adsorbate) else None
            snapshots.append(
                (item, item.name, item.properties, copy.deepcopy(item.properties), aliases, list(aliases) if aliases is not None else None)
            )
    try:
        yield
    finally:
        changed_backend = pygaps.thermodynamic_backend() != backend
        coolprop_utilities.COOLPROP_BACKEND = backend
        for item, name, properties, saved_properties, aliases, saved_aliases in snapshots:
            if isinstance(item, pygaps.Adsorbate):
                changed_fluid = item.properties.get('backend_name') != saved_properties.get('backend_name')
                if changed_backend or changed_fluid or item._backend_mode not in (None, backend) or item._state is None:
                    # Native state cannot be copied; recreate it only on the next access.
                    item._state = None
                    item._backend_mode = None
                aliases[:] = saved_aliases
                item.alias = aliases
            item.name = name
            properties.clear()
            properties.update(saved_properties)
            item.properties = properties
        for registry, members in registries:
            registry[:] = members


@contextmanager
def registered_object(registry, item):
    """Remove this registration by identity, leaving equal-name objects untouched."""
    registry.append(item)
    try:
        yield
    finally:
        for index in range(len(registry) - 1, -1, -1):
            if registry[index] is item:
                del registry[index]
                break


@contextmanager
def plotting_context(style):
    """Restore plotting configuration and converters, even when plotting fails."""
    converters = units.registry.copy()
    try:
        with warnings.catch_warnings(), matplotlib.rc_context(), mpl_style.context(style):
            yield
    finally:
        units.registry.clear()
        units.registry.update(converters)
        pyplot.close('all')


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

    def make_cleanup(func):
        if inspect.isgeneratorfunction(func):

            @functools.wraps(func)
            def wrapped_callable(*args, **kwargs):
                with plotting_context(style):
                    yield from func(*args, **kwargs)
        else:

            @functools.wraps(func)
            def wrapped_callable(*args, **kwargs):
                with plotting_context(style):
                    return func(*args, **kwargs)

        return wrapped_callable

    if callable(style):
        result = make_cleanup(style)
        # Default of mpl_test_settings fixture and image_comparison too.
        style = ["classic", "_classic_test_patch"]
        return result
    else:
        return make_cleanup

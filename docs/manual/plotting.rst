.. _plotting-manual:

Plotting
========

.. _plotting-manual-general:

Overview
--------

While the user can of course take the isotherm data and generate their own
customised plots, pyGAPS includes a few plotting functions which make it easier
for standard plots to be generated.

The main plotting tool is in the
:func:`~pygaps.graphing.isotherm_graphs.plot_iso` function, which handles the
plotting of isotherms. Some common use-case scenarios for the functionality are:

    - Visualising the data after isotherm instantiation.
    - Quickly comparing several isotherms.
    - Checking the overlap of a model isotherm and the point data.
    - Generating graphs for a publication.

The function can take many parameters which will modify the graph style, colours
etc. The function also accepts keywords to specify the unit, pressure mode and
basis of the graphs. A complete list of parameters can be found in the
:ref:`reference <plotting-ref>`.

The function also returns the ``matplotlib`` Axes, to allow for further
customisation for the resulting plot.


.. _plotting-manual-examples:

Examples
--------

Check out the Jupyter notebook in the `examples <../examples/plotting.ipynb>`_ section.

.. _plotting-manual:

Plotting
========

.. _plotting-manual-general:

Overview
--------

While the user can of course take the isotherm data and generate their own customised plots, pyGAPS
includes a few plotting functions which make it easier for standard plots to be generated.

The main plotting tool is in the :meth:`~pygaps.graphing.isothermgraphs.plot_iso` function which handles
the plotting of isotherms. Some common use-case scenarios for the functionality are:

    - Visualising the data after isotherm instantiation.
    - Quickly comparing several isotherms.
    - Checking the overlap of a model isotherm and the point data.
    - Generating graphs for a publication.

The function can take many parameters which will modify the graph style, colours etc. The function
also accepts keywords to specify the unit, pressure mode and basis of the graphs. A complete list
of parameters can be found in the :ref:`reference <isotherm-plot-ref>`.

The function also returns the ``matplotlib`` figure and ax, to allow for further customisation for the
resulting plot.


.. _plotting-manual-examples:

Examples
--------

Some examples of different graphs are shown below

    - A logarithmic isotherm graph comparing the adsorption branch of two isotherms up to 1 bar.

      ::

        pygaps.plot_iso(
            [isotherm1, isotherm2],
            branch = 'ads',
            logarithmic = True,
            xmaxrange=1
        )

    - A black and white full scale graph of both adsorption and desorption branches of an
      isotherm, saving it to the local directory for a publication.

      ::

        pygaps.plot_iso(
            [isotherm],
            branch = ['ads', 'des'],
            color=False,
            save=True,
            fig_title='Novel Behaviour'
            path=r"/mygraph/"
        )


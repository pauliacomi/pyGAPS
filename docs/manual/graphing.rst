.. _plotting-manual:

Plotting
========

Examples

    - A logarithmic isotherm graph comparing the adsorption branch of two isotherms up to 1 bar::

        pygaps.plot_iso(
            [isotherm1, isotherm2],
            branch = 'ads',
            logarithmic = True,
            xmaxrange=1
        )

    - A black and white full scale graph of both adsorption and desorption branches of an
      isotherm, saving it to the local directory for a publication::

        pygaps.plot_iso(
            [isotherm],
            branch = ['ads', 'des'],
            color=False,
            save=True,
            fig_title='Novel Behaviour'
            path=r"/mygraph/"
        )


.. _characterisation-manual:

Adsorbent characterisation
==========================

Overview
--------

The main purpose behind the pyGAPS framework is to allow standard isotherm
characterisation techniques to be carried out in bulk for high throughput
testing, as well as to disconnect adsorption data processing from the machine
used to record it.

The framework currently provides the following functionality for material
characterisation:

    - BET surface area :mod:`~pygaps.characterisation.area_bet`
    - Langmuir surface area :mod:`~pygaps.characterisation.area_langmuir`
    - The t-plot method :mod:`~pygaps.characterisation.tplot`
    - The :math:`\alpha_s` method :mod:`~pygaps.characterisation.alphas`
    - Pore size distribution (PSD) calculations

        - Mesoporous PSD calculations function
          :meth:`~pygaps.characterisation.psd_mesoporous.psd_mesoporous` with
          the module containing the individual model references:
          :mod:`pygaps.characterisation.psd_mesoporous`
        - Microporous PSD calculations function
          :meth:`~pygaps.characterisation.psd_microporous` with the module
          containing the individual model references:
          :mod:`~pygaps.characterisation.psd_microporous`
        - DFT kernel fitting PSD function
          :meth:`~pygaps.characterisation.psd_dft` with the module containing
          the individual model references:
          :mod:`~pygaps.characterisation.psd_dft`

    - Isosteric enthalpy of adsorption calculations
      :meth:`~pygaps.characterisation.isosteric_enthalpy.isosteric_enthalpy`
    - Dubinin-Radushevitch and Dubinin-Astakov plots
      (:meth:`~pygaps.characterisation.dr_da_plots.dr_plot`,
      :meth:`~pygaps.characterisation.dr_da_plots.da_plot`)
    - Initial Henry constant calculation
      :mod:`~pygaps.characterisation.initial_henry`
    - Initial enthalpy of adsorption calculation (from isotherms with enthalpy
      data) :mod:`~pygaps.characterisation.initial_enthalpy`

More info about each function and its usage can be found on their respective
page.

.. caution::

    Before using the provided characterisation functions, make sure you are
    aware of how :ref:`units <units-manual>` work and how the backend
    :ref:`calculates <eqstate-manual>` adsorbate properties.


.. _characterisation-manual-examples:

Characterisation examples
-------------------------

The best way to get familiarized with characterization functions is to check out
the Jupyter notebooks in the :ref:`examples <example-characterisation>` section.

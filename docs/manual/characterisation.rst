.. _characterisation-manual:

Adsorbent characterisation
==========================

Overview
--------

The main purpose behind the pyGAPS framework is to allow standard isotherm characterisation techniques
to be carried out in bulk for high throughput testing, as well as to disconnect adsorption data processing
from the machine used to record it.

The framework currently provides the following functionality for material characterisation:

    - BET surface area :mod:`~pygaps.calculations.area_bet`
    - Langmuir surface area :mod:`~pygaps.calculations.area_langmuir`
    - The t-plot method :mod:`~pygaps.calculations.tplot`
    - The :math:`\alpha_s` method :mod:`~pygaps.calculations.alphas`
    - Pore size distribution (PSD) calculations
        - Mesoporous PSD calculations function :meth:`~pygaps.calculations.psd.mesopore_size_distribution`
          with the module containing the individual model references: :mod:`pygaps.calculations.psd_mesoporous`
        - Microporous PSD calculations function :meth:`~pygaps.calculations.psd.micropore_size_distribution`
          with the module containing the individual model references: :mod:`~pygaps.calculations.psd_microporous`
        - DFT kernel fitting PSD function :meth:`~pygaps.calculations.psd.dft_size_distribution`
          with the module containing the individual model references: :mod:`~pygaps.calculations.psd_dft`
    - Isosteric heat of adsorption calculations :meth:`~pygaps.calculations.isosteric_heat.isosteric_heat`
    - Dubinin-Radushevitch and Dubinin-Astakov plots
      (:meth:`~pygaps.calculations.dr_da_plots.dr_plot`,
      :meth:`~pygaps.calculations.dr_da_plots.da_plot`)
    - Initial Henry constant calculation :mod:`~pygaps.calculations.initial_henry`
    - Initial enthalpy of adsorption calculation (from isotherms with enthalpy data)
      :mod:`~pygaps.calculations.initial_enthalpy`

More info about each function and its usage can be found on the respective page.

.. caution::

    Before using the provided characterisation functions, make sure you are aware
    of how :ref:`units <units-manual>` work and how the backend
    :ref:`calculates <eqstate-manual>` adsorbate properties.


.. _characterisation-manual-examples:

Characterisation examples
-------------------------

Check out the ipython notebooks in the :ref:`examples <example-characterisation>` section

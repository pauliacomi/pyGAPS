.. _characterisation-manual:

Adsorbent characterisation
==========================

Overview
--------

The main purpose behind the pyGAPS framework is to allow standard isotherm characterisation techniques
to be carried out in bulk for high throughput testing, as well as to disconnect adsorption data processing
from the machine used to record it.

The framework currently provides the following functionality:

    - BET surface area :mod:`~pygaps.calculations.bet`
    - The t-plot method :mod:`~pygaps.calculations.tplot`
    - The :math:`\alpha_s` method :mod:`~pygaps.calculations.alphas`
    - PSD (pore size distribution) calculations
        - Mesoporous PSD calculations function :meth:`~pygaps.calculations.psd.mesopore_size_distribution`
          with the module containing the individual model references: :mod:`pygaps.calculations.psd_mesoporous`
        - Microporous PSD calculations function :meth:`~pygaps.calculations.psd.micropore_size_distribution`
          with the module containing the individual model references: :mod:`~pygaps.calculations.psd_microporous`
        - DFT kernel fitting PSD function :meth:`~pygaps.calculations.psd.dft_size_distribution`
          with the module containing the individual model references: :mod:`~pygaps.calculations.psd_dft`
    - Isosteric heat of adsorption calculation :mod:`~pygaps.calculations.isosteric_heat`


More info about each function and its usage can be found on the respective page.

.. caution::

    Before using the provided characterisation functions, make sure you are aware
    of how :ref:`units work <units-manual>` and how the backend
    :ref:`calculates <eqstate-manual>` adsorbent properties.


.. _characterisation-manual-examples:

Characterisation example
------------------------

Check it out in the ipython notebooks in the :ref:`examples <example-characterisation>` section

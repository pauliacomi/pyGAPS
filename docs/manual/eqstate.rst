.. _eqstate-manual:

Equations of state
==================

In order to calculate adsorbate properties such as molar mass, vapour pressure
or surface tension, pyGAPS makes use of `CoolProp <http://www.coolprop.org/>`__
or `REFPROP <https://www.nist.gov/srd/refprop>`__. This thermodynamic backend
allows for the calculation of multiple fluid state variables.

.. note::

    Not all adsorbates have a thermodynamic backend known to CoolProp. See
    `here <http://www.coolprop.org/fluid_properties/PurePseudoPure.html#list-of-fluids>`__
    for the list of fluids. If not available, the user can provide their own static
    values for required properties :ref:`like so<adsorbate-manual-methods>`.

CoolProp has the ability to use either the open source *HEOS* or the proprietary
*REFPROP* backend. pyGAPS defaults to using the HEOS backend, but it the user
has REFPROP installed and configured on their computer, they can enable it by
using the switching function:

.. code:: python

    pygaps.backend_use_refprop()

To go back to the standard CoolProp backend, use:

.. code:: python

    pygaps.backend_use_coolprop()


.. warning::

    If REFPROP is not previously installed and configured on the user's
    computer, calculations will fail.

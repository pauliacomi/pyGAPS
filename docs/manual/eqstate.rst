.. _eqstate-manual:

Equations of state
==================

In order to calculate adsorbate properties such as molar mass, vapour pressure or surface tension, pyGAPS
makes use of `CoolProp <http://www.coolprop.org/>`__.

CoolProp has the ability to use either the *HEOS* or the *REFPROP* backend. pyGAPS defaults to using
the HEOS backend, but it the user has REFPROP installed and configured on their computer, they can enable it by
using the switching function:

::

    pygaps.backend_use_refprop()

To go back to the standard CoolProp backend, use:

::

    pygaps.backend_use_coolprop()


.. warning::

    If REFPROP is not previously installed and configured on the user's computer, calculations
    will fail.

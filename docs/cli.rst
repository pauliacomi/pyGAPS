======================
Command Line Interface
======================

Some pyGAPS functionality can also be used from the command line. Once
installed, an entrypoint is automatically generated under the name ``pygaps``.

.. code-block:: bash

    pygaps -h

Currently the CLI can read any pyGAPS format (JSON, CSV, Excel) and then:

    * print isotherm to output (default if no argument is passed)
    * plot the isotherm using a Matplotlib TKinter window (``-p/--plot``)
    * run basic automated characterization tests (``-ch/--characterize a_bet``
      for the BET area for example)
    * attempt to model the isotherm using a requested model or guess the best
      fitting model (``-md/--model guess``) and save the resulting isotherm model
      using the ``-o/--outfile`` path.
    * convert the isotherm to any unit/basis
      (``-cv/--convert pressure_mode=absolute,pressure_unit=bar``) and save the
      resulting isotherm model using the ``-o/--outfile`` path.

The ``-v/--verbose`` flag will increase verbosity, often showing result plots or
printing out different steps.

======================
Command Line Interface
======================

Some pyGAPS functionality can also be used from the command line. Once
installed, an entrypoint is automatically generated under the name ``pygaps``.

.. code-block:: bash

    pygaps -h

Full reference below:

Supported input formats are JSON, CSV, AIF, XLS and XLSX. Choose at most one
primary action: ``--plot``, ``--characterize``, ``--model`` or ``--convert``.
Without an action, the isotherm is printed. All characterization choices
(``a_bet``, ``a_lang`` and ``kh``) print their results.

Model and conversion output can be saved with ``--outfile`` in JSON, CSV,
AIF or XLSX format. A legacy ``.xls`` output path is redirected to ``.xlsx``
with a warning. Without an output path, these operations do not save a file;
use ``--verbose`` to print the resulting isotherm.

Conversion settings are comma-separated ``key=value`` pairs. Supported keys
are ``pressure_mode``, ``pressure_unit``, ``loading_basis``, ``loading_unit``,
``material_basis`` and ``material_unit``. Keys may appear only once, and values
must not be empty. Whitespace around keys and values is ignored.

.. code-block:: bash

    pygaps input.json --convert pressure_unit=Pa,loading_unit=mol --outfile converted.json

Invalid command-line options, conflicting actions, missing input files,
unsupported suffixes and invalid conversion settings produce a concise error
on standard error and exit with status 2. Scientific calculation failures
and unexpected errors remain visible rather than being converted to success
or hidden behind a generic command-line error.

Model fitting and conversion require a point isotherm. Characterization and
plotting accept point or model isotherms, but not base metadata-only isotherms.
Unsupported input kinds also produce an input error with status 2.

Python callers can pass an argument list to ``main(argv)``; omitting it keeps
the usual process command-line behavior.

.. automodule:: pygaps.cli.cli
    :members:

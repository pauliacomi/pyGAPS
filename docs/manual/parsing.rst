.. _parsing-manual:

Data import and export
======================

.. _parsing-manual-general:

Overview
--------

Besides creating an isotherm from raw data, explained in detail in
:ref:`this section <isotherms-manual-create>` of the manual, there are other
options on how to import or export isotherms.

.. include:: parsing_modes.rst
- Imported from one of many device manufacturer formats. See
  :ref:`parsing manufacturer files <parsing-manual-manufacturer>`.
- From an internal database: pyGAPS contains functionality to store and
  retrieve constructed isotherms in an sqlite database. See
  :ref:`database <parsing-manual-sqlite>`.

.. note::

    Most functions can import/export both a
    :class:`~pygaps.core.pointisotherm.PointIsotherm` and a
    :class:`~pygaps.core.modelisotherm.ModelIsotherm`.


.. _parsing-manual-json:

JSON parsing
------------

Importing and exporting isotherms in a JSON format is a great alternative to a
CSV or Excel files and is the recommended pyGAPS way of sharing isotherms. The
JSON format has several advantages, such as being a web standard, and
near-universal parsing capabilities, not to mention the ease of extensibility
afforded by the structure. An example JSON isotherm can be found
:download:`here <../files/isotherm.json>`.

.. caution::

    The JSON format is, by definition, unsorted. Therefore, even though pyGAPS
    sorts the keys alphabetically before returning the string, one should not
    rely on their order.

The framework provides two functions for JSON parsing:

- Import an isotherm from JSON: :func:`~pygaps.parsing.json.isotherm_from_json`
- Export an isotherm to JSON: :func:`~pygaps.parsing.json.isotherm_to_json`, or
  for convenience :meth:`~pygaps.core.baseisotherm.BaseIsotherm.to_json`.

Assuming we have an isotherm which was previously created, use the following
code to convert it to a JSON string or file.

.. code:: python

    import pygaps.parsing as pgp

    # to a string
    json_string = pgp.isotherm_to_json(my_isotherm)

    # to a file
    pgp.isotherm_to_json(my_isotherm, 'path/to/file.json')

    # or for convenience
    my_isotherm.to_json('path/to/file.json')

To parse JSON into an isotherm, use the *from* function.

.. code:: python

    import pygaps.parsing as pgp
    my_isotherm = pgp.isotherm_from_json(json_string_or_path)

For detailed information about JSON parsing functions, check out the
:mod:`~pygaps.parsing.json` module reference.


.. _parsing-manual-aif:

AIF parsing
-----------

The `Adsorption Information File <https://adsorptioninformationformat.com>`__
(AIF) is a recently developed file format [1]_, analogous to a Crystallographic
Information File (CIF) file. It is meant to be an extensible text file,
comprising of isotherm points and extensive metadata which facilitate the
standardisation, sharing and publication of isotherms. An example AIF can be
downloaded :download:`here <../files/isotherm.aif>`.

pyGAPS can import and export AIF through:

- Import an isotherm from AIF: :func:`~pygaps.parsing.aif.isotherm_from_aif`
- Export an isotherm to AIF: :func:`~pygaps.parsing.aif.isotherm_to_aif`, or
  for convenience :meth:`~pygaps.core.baseisotherm.BaseIsotherm.to_aif`.

Assuming we have an isotherm which was previously created, use the following
code to convert it to a AIF string or file.

.. code:: python

    import pygaps.parsing as pgp

    # to a string
    aif_string = pgp.isotherm_to_aif(my_isotherm)

    # to a file
    pgp.isotherm_to_aif(my_isotherm, 'path/to/file.aif')

    # or for convenience
    my_isotherm.to_aif('path/to/file.aif')


To parse an AIF file as an isotherm, use the *from* function.

.. code:: python

    import pygaps.parsing as pgp
    my_isotherm = pgp.isotherm_from_aif(aif_string_or_path)

For more info about AIF parsing, check out the :mod:`~pygaps.parsing.aif`
module reference.


.. [1] Evans, J. D., Volodymyr B., Irena S., and Stefan K.. "A Universal
  Standard Archive File for Adsorption Data". Langmuir, 2 April 2021, DOI:
  10.1021/acs.langmuir.1c00122


.. _parsing-manual-csv:

CSV parsing
-----------

CSV files can also be used as a convenient storage for isotherms. However, the
format is not as flexible as the alternatives. The CSV files created will have
all the isotherm metadata as key-value pairs, followed by a section which
includes the data or model of the isotherm. An example CSV isotherm can be found
:download:`here <../files/isotherm.csv>`.

The main functions pertaining to CSV parsing are:

- Import an isotherm from CSV: :func:`~pygaps.parsing.csv.isotherm_from_csv`
- Export an isotherm to CSV: :func:`~pygaps.parsing.csv.isotherm_to_csv`, or
  for convenience :meth:`~pygaps.core.baseisotherm.BaseIsotherm.to_csv`.

Assuming we have an isotherm which was previously created, use the following
code to convert it to a CSV string or file.

.. code:: python

    import pygaps.parsing as pgp

    # to a string
    csv_string = pgp.isotherm_to_csv(my_isotherm)

    # to a file
    pgp.isotherm_to_csv(my_isotherm, 'path/to/file.csv')

    # or for convenience
    my_isotherm.to_csv('path/to/file.csv')

To parse CSV into an isotherm, use the *from* function.

.. code:: python

    import pygaps.parsing as pgp
    my_isotherm = pgp.isotherm_from_csv(csv_string_or_path)

For more info about CSV parsing, check out the :mod:`~pygaps.parsing.csv`
module reference.


.. _parsing-manual-excel:

Excel parsing
-------------

The isotherms can also be imported or exported in an Excel format, if required.
This is done with the help of the ``xlrd``/``xlwt`` python packages. An example
excel isotherm can be found :download:`here <../files/isotherm.xls>`.

The framework provides two functions for Excel files:

- Import an isotherm from Excel: :func:`~pygaps.parsing.excel.isotherm_from_xl`
- Export an isotherm to Excel: :func:`~pygaps.parsing.excel.isotherm_to_xl`, or
  for convenience :meth:`~pygaps.core.baseisotherm.BaseIsotherm.to_xl`.

To export an isotherm to an Excel file, pass the isotherm object, as well as the
path where the file should be created.

.. code:: python

    import pygaps.parsing as pgp

    # export the isotherm
    pgp.isotherm_to_xl(my_isotherm, 'path/to/file.xls')

    # or for convenience
    my_isotherm.to_xl('path/to/file.xls')

To parse an Excel file as an isotherm, use the *from* function.

.. code:: python

    import pygaps.parsing as pgp
    my_isotherm = pgp.isotherm_from_xl('path/to/file.xls')

For more info about Excel parsing, check out the :mod:`~pygaps.parsing.excel`
module reference.



.. _parsing-manual-manufacturer:

Manufacturer-specific parsing
-----------------------------

Most commercial adsorption apparatus can output the recorded isotherm as an Excel
(.xls/.xlsx), a CSV (.csv) or a text file. Many of these can be imported using the
:func:`~pygaps.parsing.isotherm_from_commercial` function.

Currently pyGAPS includes functionality to import:

- SMS DVS `.xlsx` files: ``iso = isotherm_from_commercial(path, "smsdvs", "xlsx")``
- Microtrac BEL `.dat` files: ``iso = isotherm_from_commercial(path, "bel", "dat")``
- Microtrac BEL `.xls` files: ``iso = isotherm_from_commercial(path, "bel", "xl")``
- Microtrac BEL `.csv` files: ``iso = isotherm_from_commercial(path, "bel", "csv")``
- Micromeritics `.xls` files: ``iso = isotherm_from_commercial(path, "mic", "xl")``
- 3P `.xlsx` report files: ``iso = isotherm_from_commercial(path, "3p", "xl")``
- Quantachrome Raw Isotherm `.txt` files: ``iso = isotherm_from_commercial(path, "qnt", "txt-raw")``


.. _parsing-manual-isodb:

Isotherms from the NIST ISODB
-----------------------------

The NIST `ISODB <https://adsorption.nist.gov/>`__ is a database of published
adsorption isotherms. pyGAPS can pull a specific isotherm from the NIST ISODB by
using the :func:`~pygaps.parsing.isodb.isotherm_from_isodb` function. The ISODB
isotherm filename should be specified as a parameter.

.. code:: python

    import pygaps.parsing as pgp
    isotherm = pgp.isotherm_from_isodb('10.1002adfm.201200084.Isotherm3')

.. caution::

    This functionality relies on public APIs from NIST. No guarantee can be made
    regarding future availability.


.. _parsing-manual-sqlite:

Sqlite parsing
--------------

pyGAPS includes an internal sqlite database where Isotherms can be saved for
later use, as well as samples, adsorbates, etc. The database functionality is an
extensive part of the framework, and it has its own
:ref:`section of the manual<sqlite-manual>`.

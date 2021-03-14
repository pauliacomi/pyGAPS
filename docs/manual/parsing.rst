.. _parsing-manual:

Data import and export
======================

.. _parsing-manual-general:

Overview
--------

Besides the raw method of creating an isotherm, which is explained in detail in
:ref:`this section <isotherms-manual-create>` of the manual, there are other
options on how to import or export isotherms.

    - A json string or file.
    - Parsing a csv file of a standard format.
    - Parsing an excel file of a standard format.
    - Several manufacturer-specific formats from instrument outputs.
    - From an sqlite database: pyGAPS contains functionality to store and
      retrieve constructed isotherms in a sqlite database.
    - From the NIST ISODB `database <https://adsorption.nist.gov/>`__.



.. _parsing-manual-json:

JSON parsing
------------

Importing and exporting isotherms in a JSON format is a great alternative to a
CSV or XML file and is the recommended pyGAPS way of sharing isotherms. The JSON
format has several advantages of the others, such as being a standard for REST
APIs, and near-universal parsing capabilities, not to mention the ease of
extensibility afforded by the structure.

.. caution::

    The JSON format is, by definition, unsorted. Therefore, even though pyGAPS
    sorts the keys alphabetically before returning the string, one should not
    rely on their order.

The framework provides two functions for JSON strings:

    - Import an isotherm from JSON:
      :meth:`~pygaps.parsing.json.isotherm_from_json`
    - Export an isotherm to JSON: :meth:`~pygaps.parsing.json.isotherm_to_json`

Assuming we have an isotherm which was previously created, use the following
code to convert it to a JSON string. An example JSON isotherm can be found
:download:`here <../files/isotherm.json>`.

::

    # to a string
    json_string = pygaps.isotherm_to_json(my_isotherm)

    # or for convenience
    json_string = my_isotherm.to_json()

    # or to a file
    my_isotherm.to_json('path/to/file.json')


To convert the json back into an isotherm, use the *from* function.

::

    my_isotherm = pygaps.isotherm_from_json(json_string)


For more info about JSON parsing, check out the :mod:`~pygaps.parsing.json`
reference.


.. _parsing-manual-csv:

CSV parsing
-----------

CSV files can also be used as a convenient storage for isotherms. However, the
format is not as flexible as the alternatives.

The CSV files created will have all the isotherm properties as initial headers,
followed by a data section which includes the data or model of the isotherm. An
example csv isotherm can be found :download:`here <../files/isotherm.csv>`.

To export an isotherm to an CSV file, pass the isotherm object, as well as the
path where the file should be created.

::

    # to a string
    csv_string = pygaps.isotherm_to_csv(my_isotherm)

    # to a file
    pygaps.isotherm_to_csv(my_isotherm, 'path/to/file.csv')

    # or for convenience
    my_isotherm.to_csv('path/to/file.csv')

To convert the file back into an isotherm, use the *from* function.

::

    my_isotherm = pygaps.isotherm_from_csv(path)

For more info about CSV parsing, check out the
:mod:`~pygaps.parsing.csv` reference.


.. _parsing-manual-excel:

Excel parsing
-------------

The isotherms can also be imported or exported in an Excel format, if required.
This is done with the help of the xlrd/xlwt python packages. An example excel
isotherm can be found :download:`here <../files/isotherm.xls>`.

The framework provides two functions for Excel files:

    - Import an isotherm from Excel:
      :meth:`~pygaps.parsing.excel.isotherm_from_xl`
    - Export an isotherm to Excel:
      :meth:`~pygaps.parsing.excel.isotherm_to_xl`

To export an isotherm to an Excel file, pass the isotherm object, as well as the
path where the file should be created.

::

    # export the isotherm
    pygaps.isotherm_to_xl(my_isotherm, 'path/to/file.xls')

    # or for convenience
    my_isotherm.to_xl('path/to/file.xls')

To convert the excel back into an isotherm, use the *from* function.

::

    my_isotherm = pygaps.isotherm_from_xl(path)

Specific formats, such as Excel reports produced by commercial apparatus
(Micromeritics, Belsorp) can also be imported by passing in a particular format
argument. For example from a Micromeritics report:

::

    my_isotherm = pygaps.isotherm_from_xl(path, fmt='mic')


For more info about Excel parsing, check out the :mod:`~pygaps.parsing.excel`
reference.



.. _parsing-manual-manufacturer:

Manufacturer-specific parsing
-----------------------------

Most commercial apparatus can output the isotherm as Excel (xls) files. Other
machines output proprietary files which can sometimes be read and therefore
imported.

Currently pyGAPS includes functionality to import:

    - Microtrac BEL .dat files using
      :meth:`~pygaps.parsing.bel_dat.isotherm_from_bel`
    - Microtrac BEL .xls files using
      :meth:`~pygaps.parsing.excel.isotherm_from_xl` and ``fmt="bel"``
    - Micromeritics .xls files using
      :meth:`~pygaps.parsing.excel.isotherm_from_xl` and ``fmt="mic"``


.. _parsing-manual-sqlite:

Sqlite parsing
--------------

Since pyGAPS includes an internal sqlite database, isotherms which are imported
can be saved for later use, as well as samples, adsorbates, etc. The sqlite
functionality is an extensive part of the framework, and it has its own
:ref:`section <sqlite-manual>` of the manual.


.. _parsing-manual-isodb:

Isotherms from the NIST ISODB
-----------------------------

The NIST ISODB is a database of adsorption isotherms. pyGAPS can pull a specific
isotherm from the NIST ISODB by using the
:meth:`~pygaps.parsing.isodb.isotherm_from_isodb` function. The ISODB isotherm
filename should be specified as a parameter.

::

    isotherm = pygaps.isotherm_from_isodb('10.1002adfm.201200084.Isotherm3')

.. caution::

    This functionality relies on public APIs from NIST. No guarantee can be made
    regarding future availability.

.. _parsing-manual:

Data import and export
======================

.. _parsing-manual-general:

Overview
--------

Besides the raw method of creating an isotherm which is explained in detail in
:ref:`this section <isotherms-manual-create>` of the manual, there are other options on how to import or
export isotherms.

    - A json string or file.
    - Parsing an excel file of a standard format.
    - Parsing a csv file of a standard format.
    - Several manufacturer-specific formats.
    - From an sqlite database: pyGAPS contains functionality to store and retrieve constructed
      isotherms in a sqlite database.

.. _parsing-manual-sqlite:

Sqlite parsing
--------------

Since pyGAPS includes an internal sqlite database, isotherms which are imported can be saved for later use, as
well as samples, adsorbates, contacts etc.
The sqlite functionality is an extensive part of the framework, and it has its own
:ref:`section <sqlite-manual>` of the manual.


.. _parsing-manual-json:

JSON parsing
------------

Importing and exporting isotherms in a JSON format is a great alternative to a CSV or XML file and is the
recommended pyGAPS way of sharing isotherms. The JSON format has several advantages of the others, such as
being a standard for REST APIs, ease of reading and near-universal parsing capabilities, not to mention
the ease of extensibility afforded by the structure.

.. caution::

    The JSON format is, by definition, unsorted. Therefore, even though pyGAPS sorts the keys alphabetically
    before returning the string, one should not rely on their order.

The framework provides two functions for JSON strings:

    - Import an isotherm from JSON: :meth:`~pygaps.parsing.jsoninterface.isotherm_from_json`
    - Export an isotherm to JSON: :meth:`~pygaps.parsing.jsoninterface.isotherm_to_json`

Assuming we have an isotherm which was previously created, use the following code to convert it to
a JSON string.
An example JSON isotherm can be found :download:`here <../files/isotherm.json>`.

::

    json_string = pygaps.isotherm_to_json(my_isotherm)


To convert the json back into an isotherm, use the *from* function.

::

    my_isotherm = pygaps.isotherm_from_json(json_string)

Or alternatively with the class method:

::

    my_isotherm = pygaps.PointIsotherm.from_json(json_string)

For more info about JSON parsing, check out the :mod:`~pygaps.parsing.jsoninterface` reference.


.. _parsing-manual-excel:

Excel parsing
-------------

The isotherms can also be imported or exported in an Excel format,
if required. This is done with the help of the xlrd/xlwt python packages.
An example excel isotherm can be found :download:`here <../files/isotherm.xls>`.

The framework provides two functions for Excel files:

    - Import an isotherm from Excel: :meth:`~pygaps.parsing.excelinterface.isotherm_from_xl`
    - Export an isotherm to Excel: :meth:`~pygaps.parsing.excelinterface.isotherm_to_xl`

To export an isotherm to an Excel file, pass the isotherm object, as well as the path where the excel file
should be created.

::

    # create the path
    path = r'C:\\myisotherm.xls'

    # export the isotherm
    pygaps.isotherm_to_xl(my_isotherm, path)

To convert the excel back into an isotherm, use the *from* function.

::

    my_isotherm = pygaps.isotherm_from_xl(path)

Specific formats, such as Excel reports produced by commercial apparatus
(Micromeritics, Belsorp) can also be imported by passing in a particular
format argument. For example from a Micromeritics report:

::

    my_isotherm = pygaps.isotherm_from_xl(path, fmt='mic')


For more info about Excel parsing, check out the :mod:`~pygaps.parsing.excelinterface` reference.


.. _parsing-manual-csv:

CSV parsing
-----------

CSV files can also be used as a convenient storage for isotherms. However, the format is not as flexible
as the alternatives.

The CSV files created will have all the isotherm properties as initial headers, followed by a data section which
includes all the data in the isotherm.
An example csv isotherm can be found :download:`here <../files/isotherm.csv>`.

To export an isotherm to an CSV file, pass the isotherm object, as well as the path where the file
should be created.

::

    # create the path
    path = r'C:\\myisotherm.csv'

    # export the isotherm
    pygaps.isotherm_to_csv(my_isotherm, path)

To convert the file back into an isotherm, use the *from* function.

::

    my_isotherm = pygaps.isotherm_from_csv(path)

For more info about CSV parsing, check out the :mod:`~pygaps.parsing.csvinterface` reference.


.. _parsing-manual-manufacturer:

Manufacturer-specific parsing
-----------------------------

Most commercial apparatus can output the isotherm as Excel (xls) files.
To import these files consult the Excel parsing section. Other
machines output proprietary files which can nevertheless be imported.

Currently pyGAPS includes functionality to import:

    - Microtrac BEL .dat files using :meth:`~pygaps.parsing.csv_bel_parser.isotherm_from_bel`


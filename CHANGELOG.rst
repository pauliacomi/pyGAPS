
Changelog
=========


1.3.0 (2018-08-13)
------------------

Features:

* Added an excel import which can take Micromeritics or
  Belsorp report (.xls) files. Micromeritics code was
  taken from the `official python repo <https://github.com/Micromeritics/micromeritics>`_.
* Added an import option which can read and import Belsorp
  data (.DAT) files.
* Improved plotting functions to allow for more customisation
  over how the graph looks.
* The extra arguments to print_info() are now passed to the plotting
  function allowing for styles such as :issue:`8`.

Breaking changes:

* The unique isotherm ID is now generated only on a small subset of
  properties instead of all isotherm properties.
* The isotherm 'other_properties' subdictionary has been removed.
  Instead, all isotherm properties are now direct members of the
  class.
* When plotting, isotherm branches are now defined as 'ads', 'des'
  'all' (both branches) and 'all-nol' (both branches without
  legend entry) instead of a list of branches.
* Plot types are now universal. Any property can be plotted
  against any other property by specifying the x_data,
  y1_data and y2_data.

Bugfixes:

* Fixed 'source' not being recognised as an isotherm field
* Added correct common name for ethylene, propylene, methanol
  and ethanol in the database
* Renamed some model parameters for consistency
* A lot of typo fixes


1.2.0 (2018-02-19)
------------------

Features:

* The plotting legend now works with any isotherm attribute specified
* Changed model parent class to print out model name when displayed
* Added Toth and Jensen-Seaton models to the IAST calculation (spreading pressure is computed
  numerically using scipy.integrate.quad, :issue:`7`)

Bugfixes:

* Fixed an issue where the returned IAST selectivity v pressure data would not include all pressures
* Changed sqlite retrieval order to improve performance (:issue:`2`)
* Fixed an error where IAST vle data was plotted opposite to the graph axes
* Fixed a mistake in the Jensen-Seaton equation
* Fixed a mistake in the FH-VST equation

1.1.1 (2018-02-11)
------------------

Features:

* Allowed for branch selection for isosteric heat and fixed an error where this was an issue (:issue:`3`)

Bugfixes:

* Fixed an issue when plotting isotherms with and without secondary data simultaneously
* Fixed error with magnitude of polarizability of adsorbate from database in microporous PSD


1.1.0 (2018-01-24)
------------------

* Automatic travis deployment to PyPI
* Improved enthalpy modelling for initial enthalpy determination
* Improved documentation

1.0.1 (2018-01-08)
------------------

* Fixed wrong value of polarizability for nitrogen in database
* Added a check for initial enthalpy when the isotherm is measured in supercritical mode

1.0.0 (2018-01-01)
------------------

* Improved unit management by adding a unit/basis for both the
  adsorbent (ex: amount adsorbed per g, kg or cm3 of material
  are all valid) and loading (ex: mmol, g, kg of gas adsorbed
  per amount of material are all valid)
* Separated isotherm models so that they can now be easily
  created by the used.
* Added new isotherm models: Toth, Jensen-Seaton, W-VST, FH-VST.
* Made creation of classes (Adsorbate/Sample/Isotherms) more
  intuitive.
* Many small fixes and improvements

0.9.3 (2017-10-24)
------------------

* Added unit_adsorbate and basis_loading as parameters for an isotherm,
  although they currently do not have any influence on data processing

0.9.2 (2017-10-24)
------------------

* Slightly changed json format for efficiency

0.9.1 (2017-10-23)
------------------

* Better examples
* Small fixes and improvements

0.9.0 (2017-10-20)
------------------

* Code is now in mostly working state.
* Manual and reference are built.


0.1.0 (2017-07-27)
------------------

* First release on PyPI.
